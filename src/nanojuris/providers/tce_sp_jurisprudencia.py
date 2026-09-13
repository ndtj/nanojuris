"""TCE-SP public jurisprudence catalog provider."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import DocumentReference, fetch_document_reference
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
    CanonicalDocument,
    DecisionBundle,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient, TransportPolicy
from nanojuris.transport.models import TransportRequest, TransportStatus


class TceSpJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for public TCE-SP jurisprudence summaries and bulletins."""

    name = "tce_sp_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tce_sp_url).hostname or ""
        self._document_policy = TransportPolicy(
            allowed_hosts=(host,),
            timeout_seconds=self.config.timeout,
            max_retries=2,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self._listing_transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=8_000_000,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._document_urls: dict[str, str] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        selected_types = _selected_types(query.types)
        trace = SourceTrace(
            provider=self.name,
            endpoint="/boletim-de-jurisprudencia/(sumulas|publicacoes)",
            query=query.to_dict(),
            source_url=self.config.tce_sp_url,
            limitations=[
                "Catalogos publicos do TCE-SP validados com sessao HTTP limpa.",
                "A busca dinamica /jurisprudencia/pesquisar contem reCAPTCHA e nao e automatizada.",
            ],
        )
        results: list[JurisprudenceResult] = []
        if "sumula" in selected_types:
            html, source_url = self._request_text("GET", "/boletim-de-jurisprudencia/sumulas")
            results.extend(parse_tce_sp_sumulas(html, source_url=source_url, trace=trace))
        if "boletim" in selected_types:
            html, source_url = self._request_text("GET", "/boletim-de-jurisprudencia/publicacoes")
            results.extend(parse_tce_sp_boletins(html, source_url=source_url, trace=trace))
        if "indice_remissivo" in selected_types:
            results.extend(self.get_index())

        for result in results:
            document_url = result.document_url or str(result.raw.get("document_url") or "")
            if document_url:
                self._document_urls[result.id] = document_url

        normalized_query = _normalize_text(query.text or query.exact_phrase)
        if normalized_query:
            results = [
                result
                for result in results
                if normalized_query
                in _normalize_text(
                    " ".join(
                        str(value or "")
                        for value in [
                            result.summary,
                            result.thesis,
                            result.question,
                            result.raw,
                        ]
                    )
                )
            ]

        start_index = (query.page - 1) * query.page_size
        limited = results[start_index : start_index + query.page_size]
        start = start_index + 1 if limited else 0
        return SearchPage(
            source=self.name,
            total=len(results),
            start=start,
            end=start + len(limited) - 1 if limited else 0,
            page=query.page,
            page_size=query.page_size,
            results=limited,
            source_trace=trace,
            pagination_mode="local_window",
            is_complete=True,
            completeness_reason=(
                "Os catálogos públicos completos foram carregados e filtrados localmente."
            ),
            total_known=True,
            access_status=AccessStatus.PUBLIC,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        if not precedent_id.startswith("https://") and precedent_id not in self._document_urls:
            return DecisionBundle(
                precedent_id=precedent_id,
                source=self.name,
                texts=[],
                raw={
                    "message": (
                        "TCE-SP sumulas possuem enunciado inline; somente boletins "
                        "com URL observada oferecem documento separado."
                    )
                },
            )
        document = self.get_document(precedent_id)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document.text or "",
                    "content_type": document.content_type or "text/plain",
                }
            ],
            source_trace=document.source_trace,
            raw={"document": document.raw_metadata},
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Fetch a bulletin URL observed in the current public catalog.

        The search result is the authority for the URL; opaque identifiers are
        never expanded into guessed routes.  Direct HTTPS URLs are accepted
        only when they belong to the configured TCE-SP host.
        """

        document_url = (
            document_id
            if document_id.startswith("https://")
            else self._document_urls.get(document_id)
        )
        if not document_url:
            raise ValueError(
                "TCE-SP document_id must be an observed bulletin URL or a result id "
                "from the current search"
            )
        parsed = urlparse(document_url)
        expected_host = urlparse(self.config.tce_sp_url).hostname
        if parsed.hostname != expected_host:
            raise ValueError("TCE-SP document URL is outside the configured allowlist")
        reference = DocumentReference(
            id=document_id,
            source=self.name,
            url=document_url,
            expected_content_types=("text/html", "text/plain", "application/pdf"),
        )
        return fetch_document_reference(
            reference,
            policy=self._document_policy,
            session=self.session,
            title=f"TCE-SP boletim {parsed.path.rsplit('/', 1)[-1]}",
        )

    def get_catalog(self) -> ProviderCatalog:
        """Expose the public TCE-SP bulletin collection as a typed catalog.

        The dynamic search route is protected by reCAPTCHA. The two public
        bulletin pages are stable, read-only alternatives and already power
        ``search``; exposing them here makes the available species explicit
        without pretending that a protected search endpoint is available.
        """

        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /boletim-de-jurisprudencia/{sumulas|publicacoes}",
            query={"catalog": True},
            source_url=self.config.tce_sp_url,
            limitations=[
                "Catalogo formado pelas colecoes publicas de sumulas e boletins.",
                "A busca dinamica do TCE-SP permanece protegida por reCAPTCHA.",
            ],
        )
        sumulas_html, sumulas_url = self._request_text("GET", "/boletim-de-jurisprudencia/sumulas")
        boletins_html, boletins_url = self._request_text(
            "GET", "/boletim-de-jurisprudencia/publicacoes"
        )
        sumulas = parse_tce_sp_sumulas(sumulas_html, source_url=sumulas_url, trace=trace)
        boletins = parse_tce_sp_boletins(boletins_html, source_url=boletins_url, trace=trace)
        for result in boletins:
            document_url = result.document_url or str(result.raw.get("document_url") or "")
            if document_url:
                self._document_urls[result.id] = document_url
        return ProviderCatalog(
            source=self.name,
            courts=[
                ProviderOption(
                    code="TCE-SP",
                    description="Tribunal de Contas do Estado de Sao Paulo",
                )
            ],
            species=[
                ProviderOption(code="sumula", description="Súmula"),
                ProviderOption(
                    code="boletim_jurisprudencia",
                    description="Boletim de jurisprudência",
                ),
            ],
            species_groups=[
                {"name": "sumulas", "count": len(sumulas)},
                {"name": "boletins", "count": len(boletins)},
            ],
            source_trace=trace,
            raw={
                "sumulas": [item.to_dict() for item in sumulas],
                "boletins": [item.to_dict() for item in boletins],
            },
        )

    def get_index(self) -> list[JurisprudenceResult]:
        """Return the official alphabetical/remissive index window.

        The index is a public, read-only route distinct from the protected
        dynamic search. Each topic is linked to the bulletin edition observed
        by the source; no URL is guessed and the raw relationship is preserved.
        """

        source_path = "/boletim-de-jurisprudencia/indice-alfabetico-remissivo"
        html, source_url = self._request_text("GET", source_path)
        trace = SourceTrace(
            provider=self.name,
            endpoint=source_path,
            query={"collection": "indice_remissivo"},
            source_url=source_url,
            limitations=[
                "Indice remissivo oficial aponta para edicoes de boletins; "
                "nao substitui a busca dinamica protegida por reCAPTCHA."
            ],
        )
        return parse_tce_sp_indice(html, source_url=source_url, trace=trace)

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TCE-SP Jurisprudencia",
            source_url=self.config.tce_sp_url.rstrip("/") + "/boletim-de-jurisprudencia",
            category="administrative_jurisprudence",
            search_modes=["text", "catalog", "document_type", "indice_remissivo"],
            document_types=["sumula", "boletim_jurisprudencia", "indice_remissivo"],
            content_formats=["html"],
            canonical_records=["CanonicalPrecedent", "CanonicalDocument"],
            extracted_fields=[
                "id",
                "summary_number",
                "statement",
                "history",
                "foundation",
                "bulletin_edition",
                "bulletin_url",
                "document_url",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /boletim-de-jurisprudencia/sumulas",
                "GET /boletim-de-jurisprudencia/publicacoes",
                "GET /boletim-de-jurisprudencia/indice-alfabetico-remissivo",
            ],
            supports_full_text=True,
            pagination_mode="local_window",
            completeness_contract="observed_window_only",
            full_text_access="document_link",
            supports_cli=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=["text", "types"],
            filter_semantics={
                "text": "local_postfilter",
                "exact_phrase": "local_postfilter",
                "types": "translated",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                **{
                    name: "unsupported"
                    for name in (
                        "courts",
                        "all_words",
                        "any_words",
                        "without_words",
                        "rapporteur",
                        "updated_from",
                        "updated_to",
                        "published_from",
                        "published_to",
                        "number",
                        "case_class",
                        "judging_body",
                        "degree",
                        "instance",
                        "legal_area",
                        "decision_type",
                        "judgment_date_from",
                        "judgment_date_to",
                        "source_origin",
                        "source_origins",
                        "fetch_details",
                        "party_name",
                        "party_document",
                        "lawyer_name",
                        "oab",
                        "precatory_number",
                        "police_document",
                        "cda",
                    )
                },
            },
            limitations=[
                "Provider usa catalogos estaticos; busca dinamica com reCAPTCHA "
                "nao e automatizada.",
                "Boletins sao listados por URL publica; texto integral pode variar por pagina.",
            ],
            responsible_use=[
                "Preservar URL publica e SourceTrace para auditoria.",
                "Nao tentar resolver reCAPTCHA da busca dinamica do TCE-SP.",
            ],
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> tuple[str, str]:
        url = urljoin(self.config.tce_sp_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        headers.update(kwargs.pop("headers", {}))
        request = TransportRequest(
            source=self.name,
            operation=f"{method.lower()}_{path.lstrip('/').replace('/', '_')}",
            method=method,
            url=url,
            params=kwargs.pop("params", {}),
            data=kwargs.pop("data", None),
            json_body=kwargs.pop("json", None),
            headers=headers,
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported TCE-SP transport arguments: {sorted(kwargs)}")
        try:
            response = self._listing_transport.request(request)
        except (requests.RequestException, SourceUnavailableError) as exc:
            raise SourceUnavailableError(f"TCE-SP jurisprudence request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                "TCE-SP jurisprudence transport failed: "
                f"{response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("TCE-SP jurisprudence transport returned no HTTP status")
        if response.status_code == 429:
            raise RateLimitDetectedError("TCE-SP jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError(
                f"TCE-SP jurisprudence requires access validation (HTTP {response.status_code})"
            )
        if response.status_code >= 500:
            raise SourceUnavailableError(
                f"TCE-SP jurisprudence returned HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TCE-SP jurisprudence rejected request with HTTP {response.status_code}"
            )
        return response.text, str(response.final_url or url)


def parse_tce_sp_sumulas(
    html: str,
    *,
    source_url: str,
    trace: SourceTrace,
) -> list[JurisprudenceResult]:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article")
    if not isinstance(article, Tag):
        raise ParserContractChangedError("TCE-SP sumulas article not found")
    text = _clean_text(article.get_text(" ", strip=True))
    matches = list(re.finditer(r"S[ÚU]MULA\s+N[ºO]\s*(\d+)\s*-\s*", text, flags=re.I))
    if not matches:
        raise ParserContractChangedError("TCE-SP sumulas not found")
    results: list[JurisprudenceResult] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        number = int(match.group(1))
        block = _clean_text(text[start:end])
        statement = _clean_text(block.split("(Veja histórico", 1)[0])
        history = _extract_table_after_heading(article, index)
        result_trace = SourceTrace(
            provider=trace.provider,
            endpoint="/boletim-de-jurisprudencia/sumulas",
            query={"sumula": number},
            source_url=source_url,
            limitations=trace.limitations,
        )
        results.append(
            JurisprudenceResult(
                id=f"tce-sp-sumula-{number}",
                source="tce_sp_jurisprudencia",
                court="TCE-SP",
                type="sumula",
                number=number,
                thesis=statement,
                summary=f"Súmula nº {number} - {statement}",
                source_trace=result_trace,
                raw={"statement": statement, "history": history, "source_url": source_url},
            )
        )
    return results


def parse_tce_sp_boletins(
    html: str,
    *,
    source_url: str,
    trace: SourceTrace,
) -> list[JurisprudenceResult]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[JurisprudenceResult] = []
    seen: set[str] = set()
    for node in soup.find_all("a", href=True):
        title = _clean_text(node.get_text(" ", strip=True))
        if "Boletim" not in title or "Jurisprudência" not in title:
            continue
        url = urljoin(source_url, str(node.get("href") or ""))
        if url in seen:
            continue
        seen.add(url)
        edition = _extract_edition(title)
        # Navigation links (including the collection landing page) can contain
        # the same words but are not bulletin documents.  Only edition links
        # are eligible for document fetch and canonicalization.
        if edition is None:
            continue
        result_trace = SourceTrace(
            provider=trace.provider,
            endpoint="/boletim-de-jurisprudencia/publicacoes",
            query={"edition": edition},
            source_url=url,
            limitations=trace.limitations,
        )
        results.append(
            JurisprudenceResult(
                id=f"tce-sp-boletim-{edition or len(results) + 1}",
                source="tce_sp_jurisprudencia",
                court="TCE-SP",
                type="boletim_jurisprudencia",
                number=edition,
                summary=title,
                source_trace=result_trace,
                raw={"title": title, "document_url": url, "source_url": source_url},
            )
        )
    if not results:
        raise ParserContractChangedError("TCE-SP boletim links not found")
    return results


def parse_tce_sp_indice(
    html: str,
    *,
    source_url: str,
    trace: SourceTrace,
) -> list[JurisprudenceResult]:
    """Parse the public alphabetical/remissive topic index."""

    soup = BeautifulSoup(html, "html.parser")
    headings = soup.select("h2.sec-titulo-separador")
    if not headings:
        raise ParserContractChangedError("TCE-SP indice remissivo headings not found")
    results: list[JurisprudenceResult] = []
    for heading in headings:
        topic = _clean_text(heading.get_text(" ", strip=True))
        link = heading.find_next("a", href=True)
        if not topic or not isinstance(link, Tag):
            raise ParserContractChangedError(
                "TCE-SP indice remissivo topic without official bulletin link"
            )
        title = _clean_text(link.get_text(" ", strip=True))
        edition = _extract_edition(title)
        if edition is None:
            raise ParserContractChangedError(
                "TCE-SP indice remissivo link without bulletin edition"
            )
        document_url = urljoin(source_url, str(link.get("href") or ""))
        result_trace = SourceTrace(
            provider=trace.provider,
            endpoint="/boletim-de-jurisprudencia/indice-alfabetico-remissivo",
            query={"topic": topic, "edition": edition},
            source_url=document_url,
            limitations=trace.limitations,
        )
        slug = re.sub(r"[^a-z0-9]+", "-", _normalize_text(topic)).strip("-")
        results.append(
            JurisprudenceResult(
                id=f"tce-sp-indice-{slug}",
                source="tce_sp_jurisprudencia",
                court="TCE-SP",
                type="indice_remissivo",
                number=edition,
                summary=topic,
                thesis=topic,
                document_url=document_url,
                source_trace=result_trace,
                raw={
                    "topic": topic,
                    "bulletin_title": title,
                    "bulletin_edition": edition,
                    "document_url": document_url,
                    "source_url": source_url,
                },
            )
        )
    return results


def _selected_types(values: list[str]) -> list[str]:
    selected: list[str] = []
    for value in values:
        normalized = _normalize_text(value).replace(" ", "_")
        if normalized in {
            "sumula",
            "boletim",
            "boletim_jurisprudencia",
            "indice",
            "indice_remissivo",
        }:
            if normalized.startswith("indice"):
                selected.append("indice_remissivo")
                continue
            selected.append("boletim" if normalized.startswith("boletim") else normalized)
    return selected or ["sumula", "boletim"]


def _extract_table_after_heading(article: Tag, index: int) -> str | None:
    tables = article.find_all("table")
    if index < len(tables):
        return _clean_text(tables[index].get_text(" ", strip=True))
    return None


def _extract_edition(title: str) -> int | None:
    match = re.search(r"(?:N[.ºo]*|Edição\s+N[.ºo]*)\s*(\d+)", title, flags=re.I)
    return int(match.group(1)) if match else None


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_text(value: object) -> str:
    normalized = _clean_text(str(value or "")).casefold()
    replacements = {
        "á": "a",
        "à": "a",
        "â": "a",
        "ã": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for original, replacement in replacements.items():
        normalized = normalized.replace(original, replacement)
    return normalized
