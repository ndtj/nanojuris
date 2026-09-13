"""TRT2 BASIS public curated jurisprudence bulletin adapter.

The TRT2 PJe jurisprudence search exposes a challenge on its document route.
The official BASIS repository is a separate, public DSpace collection that
publishes selected TRT2 jurisprudence bulletins and their PDF documents.  This
provider intentionally models that curated collection; it does not claim to
replace the complete PJe search surface.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import build_canonical_document
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
    CanonicalDocument,
    DecisionBundle,
    ExtractionStatus,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import (
    SharedHttpClient,
    TransportPolicy,
    TransportRequest,
    TransportResponse,
    TransportStatus,
)

SEARCH_PATH = "/discover"
COLLECTION_SCOPE = "123456789/16181"
MAX_PAGE_SIZE = 100
MAX_HTML_BYTES = 4_000_000
MAX_DOCUMENT_BYTES = 40_000_000
_OFFICIAL_HOST = "basis.trt2.jus.br"
_TITLE_RE = re.compile(r"boletim\s+de\s+jurisprud(?:e|ê)ncia\s+do\s+trt\s*2", re.I)
_CASE_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.5\.02\.\d{4}\b")
_DATE_RE = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")


class Trt2BasisJurisprudenciaProvider(JurisprudenceProvider):
    """Search selected TRT2 jurisprudence bulletins in the official BASIS."""

    name = "trt2_basis_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_http: dict[str, Any] = {}
        self._items: dict[str, dict[str, Any]] = {}
        host = urlparse(self.config.trt2_basis_jurisprudencia_url).hostname or _OFFICIAL_HOST
        self._listing_transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_HTML_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._document_transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_DOCUMENT_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    @property
    def base_url(self) -> str:
        return self.config.trt2_basis_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        page_size = min(max(query.page_size, 1), MAX_PAGE_SIZE)
        params = {
            "rpp": str(MAX_PAGE_SIZE),
            "etal": "0",
            "query": query.exact_phrase or query.text or query.number,
            "scope": COLLECTION_SCOPE,
            "group_by": "none",
            "page": str(query.page - 1),
        }
        response = self._request(SEARCH_PATH, params=params)
        # Parse the original bytes so BeautifulSoup can honor the source
        # charset declaration; requests' guessed ``text`` encoding can turn
        # Portuguese titles into mojibake and hide valid bulletin matches.
        cards, has_next = _parse_search(response.body, self.base_url)
        trace = self._trace(query, params)
        results: list[JurisprudenceResult] = []
        for card in cards:
            result = _parse_card(card, trace, self.base_url)
            if result is None:
                continue
            results.append(result)
            self._items[result.id] = {
                "pdf_url": result.document_url,
                "handle_url": result.raw.get("handle_url"),
                "title": result.raw.get("title"),
                "trace": trace,
            }
        results = results[:page_size]
        # DSpace does not expose an authoritative total for this curated
        # collection. A page without cards is therefore an unconfirmed empty
        # response, not proof that the query has no matches.
        page_complete = bool(results) and not has_next
        return SearchPage(
            source=self.name,
            total=len(results),
            start=(query.page - 1) * page_size,
            end=(query.page - 1) * page_size + len(results),
            page=query.page,
            page_size=page_size,
            results=results,
            source_trace=trace,
            pagination_mode="dspace_page",
            is_complete=page_complete,
            completeness_reason=(
                "a fonte não informa total confiável após o filtro curado"
                if has_next
                else "última página observada da busca DSpace"
            ),
            ordering="source_relevance",
            filters_applied={
                "text": "native",
                "exact_phrase": "native_as_query",
                "number": "native_as_query",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "page": "native",
            },
            total_known=False,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE if results else ExtractionStatus.PARTIAL,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document = self.get_document(precedent_id)
        text = document.text or ""
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            procedural_follow_url=document.url,
            texts=[
                {
                    "content": text,
                    "content_type": "text/plain",
                    "source_content_type": document.content_type,
                }
            ],
            source_trace=document.source_trace,
            raw={"document_url": document.url, "pdf_bytes": document.byte_size},
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        item = self._items.get(document_id)
        if item is None or not item.get("pdf_url"):
            raise SourceUnavailableError(
                "TRT2 BASIS detalhe disponível somente após uma busca na mesma sessão"
            )
        pdf_url = str(item["pdf_url"])
        response = self._request_absolute(pdf_url, max_bytes=MAX_DOCUMENT_BYTES)
        content = response.body
        if not content.startswith(b"%PDF"):
            raise ParserContractChangedError("TRT2 BASIS não retornou um PDF no link oficial")
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="boletim_jurisprudencia",
            content=content,
            content_type=response.content_type or "application/pdf",
            title=str(item.get("title") or "Boletim de Jurisprudência TRT2"),
            url=pdf_url,
            source_trace=self._detail_trace(item["trace"], pdf_url),
            access_status=AccessStatus.PUBLIC,
            raw_metadata={
                "handle_url": item.get("handle_url"),
                "collection_scope": COLLECTION_SCOPE,
            },
            parser="trt2_basis_jurisprudencia.pdf",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TRT2 BASIS — Boletins de Jurisprudência",
            source_url=f"{self.base_url}/handle/{COLLECTION_SCOPE}",
            category="curated_jurisprudence",
            search_modes=["text", "case_number", "summary", "full_text", "pagination"],
            document_types=["acordao_ementa", "boletim_jurisprudencia"],
            content_formats=["html", "pdf", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator=(
                "selected TRT2 appellate ementas published in official bulletins; "
                "not a complete PJe search"
            ),
            extracted_fields=[
                "case_number",
                "publication_date",
                "summary",
                "full_text",
                "document_url",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /discover",
                "GET /handle/123456789/16181/browse",
                "GET /bitstream/handle/{handle}/document.pdf",
            ],
            supports_full_text=True,
            full_text_access="document_link",
            # Keep the source opt-in until a current bounded call produces a
            # parsed bulletin. The route is implemented and visible in the
            # catalog, but a transient live timeout must not enter the default
            # federated rollout.
            supports_unified_search=False,
            opt_in_unified_search=True,
            supports_mcp=True,
            supports_cli=True,
            supports_live_tests=True,
            pagination_mode="dspace_page",
            max_remote_page_size=MAX_PAGE_SIZE,
            completeness_contract="dspace_total_unknown_curated_scope",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "document_type",
                "page",
            ],
            unsupported_filters=[
                "all_words",
                "any_words",
                "without_words",
                "courts",
                "types",
                "case_class",
                "judging_body",
                "rapporteur",
                "published_from",
                "published_to",
                "judgment_date_from",
                "judgment_date_to",
                "updated_from",
                "updated_to",
                "party_name",
                "party_document",
                "lawyer_name",
                "oab",
                "cda",
                "decision_type",
                "legal_area",
                "police_document",
                "precatory_number",
                "source_origin",
                "source_origins",
                "fetch_details",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "native_as_query",
                "number": "native_as_query",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "page": "native",
            },
            limitations=[
                "A coleção é curada e contém boletins selecionados, não o acervo completo do PJe.",
                "A busca DSpace não fornece total confiável após filtrar somente "
                "boletins de jurisprudência.",
                "O inteiro teor é o PDF oficial do boletim; o resultado inicial "
                "contém apenas o trecho indexado.",
            ],
            responsible_use=[
                "Usar chamadas públicas bounded, respeitar o intervalo configurado "
                "e não baixar o acervo em massa."
            ],
        )

    def _request(self, path: str, **kwargs: Any) -> TransportResponse:
        url = path if path.startswith("http") else urljoin(self.base_url + "/", path.lstrip("/"))
        return self._request_absolute(url, **kwargs)

    def _request_absolute(
        self,
        url: str,
        *,
        max_bytes: int = MAX_HTML_BYTES,
        **kwargs: Any,
    ) -> TransportResponse:
        parsed = urlparse(url)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() != _OFFICIAL_HOST:
            raise QueryRejectedError("TRT2 BASIS URL fora da allowlist oficial")
        transport = (
            self._document_transport if max_bytes > MAX_HTML_BYTES else self._listing_transport
        )
        response = transport.request(
            TransportRequest(
                source=self.name,
                operation="basis_request",
                method="GET",
                url=url,
                params=dict(kwargs.get("params") or {}),
            )
        )
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(f"TRT2 BASIS transport failed: {response.status.value}")
        final = urlparse(str(response.final_url or url))
        if final.scheme != "https" or (final.hostname or "").lower() != _OFFICIAL_HOST:
            raise SourceUnavailableError("TRT2 BASIS redirecionou para host não autorizado")
        self._last_http = {
            "http_status": response.status_code,
            "final_url": str(response.final_url or url),
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
        }
        status = int(response.status_code or 0)
        if status == 429:
            raise RateLimitDetectedError("TRT2 BASIS returned HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TRT2 BASIS returned HTTP {status}")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TRT2 BASIS returned HTTP {status}")
        return response

    def _trace(self, query: JurisprudenceQuery, params: dict[str, str]) -> SourceTrace:
        return SourceTrace(
            provider=self.name,
            endpoint=f"GET {SEARCH_PATH}",
            query={**params, "page": query.page, "page_size": query.page_size},
            source_url=urljoin(self.base_url + "/", SEARCH_PATH.lstrip("/")),
            limitations=["escopo fixo da coleção oficial de boletins de jurisprudência"],
            retrieval_status="ok",
            **self._last_http,
        )

    def _detail_trace(self, search_trace: SourceTrace, url: str) -> SourceTrace:
        return SourceTrace(
            provider=self.name,
            endpoint=f"GET {url}",
            query=search_trace.query,
            source_url=url,
            limitations=search_trace.limitations,
            retrieval_status="ok",
            transformations=["dspace_pdf_fetch", "pdf_text_extraction"],
            **self._last_http,
        )


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TRT2 BASIS exige termo, número ou frase exata")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TRT2 BASIS suporta somente segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TRT2 BASIS suporta somente instância de segundo grau")
    if query.branch and query.branch.casefold() not in {"labor", "trabalhista"}:
        raise QueryRejectedError("TRT2 BASIS pertence ao ramo trabalhista")
    if query.authority and query.authority.casefold() not in {"trt2", "trt-2", "trt 2"}:
        raise QueryRejectedError("a autoridade solicitada não corresponde ao TRT2")
    if query.collection and query.collection.casefold() not in {
        "boletim_jurisprudencia",
        "jurisprudencia",
        "cjsg_curated_bulletin",
    }:
        raise QueryRejectedError("TRT2 BASIS suporta somente a coleção de boletins")
    if query.document_type and query.document_type.casefold() not in {
        "acordao",
        "acordao_ementa",
        "boletim_jurisprudencia",
        "ementa",
    }:
        raise QueryRejectedError("TRT2 BASIS não possui esse tipo documental")
    unsupported = {
        "all_words": query.all_words,
        "any_words": query.any_words,
        "without_words": query.without_words,
        "published_from": query.published_from,
        "published_to": query.published_to,
        "judgment_date_from": query.judgment_date_from,
        "judgment_date_to": query.judgment_date_to,
        "updated_from": query.updated_from,
        "updated_to": query.updated_to,
        "case_class": query.case_class,
        "judging_body": query.judging_body,
        "rapporteur": query.rapporteur,
        "cda": query.cda,
        "decision_type": query.decision_type,
        "legal_area": query.legal_area,
        "police_document": query.police_document,
        "precatory_number": query.precatory_number,
        "source_origin": query.source_origin,
        "source_origins": query.source_origins,
        "fetch_details": query.fetch_details,
    }
    if any(value for value in unsupported.values()):
        names = ", ".join(name for name, value in unsupported.items() if value)
        raise QueryRejectedError(f"TRT2 BASIS não suporta filtro(s): {names}")


def _parse_search(html: str | bytes, base_url: str) -> tuple[list[Tag], bool]:
    soup = BeautifulSoup(html, "html.parser")
    cards = list(soup.select("div.ds-artifact-item"))
    if not cards:
        if "Pesquisa" not in soup.get_text(" ", strip=True):
            raise ParserContractChangedError("TRT2 BASIS não retornou uma página de pesquisa")
        return [], False
    has_next = any(
        "page=" in str(link.get("href", ""))
        and re.search(r"page=\d+", str(link.get("href", "")))
        and (link.get_text(" ", strip=True) in {"›", ">", "Próximo", "Next"})
        for link in soup.find_all("a", href=True)
    )
    return cards, has_next


def _parse_card(card: Tag, trace: SourceTrace, base_url: str) -> JurisprudenceResult | None:
    title_node = card.select_one("h4.artifact-title")
    title = " ".join(title_node.get_text(" ", strip=True).split()) if title_node else ""
    if not _TITLE_RE.search(title):
        return None
    handle = card.select_one('a[href*="/handle/"]')
    handle_url = urljoin(base_url + "/", str(handle.get("href")) if handle else "")
    handle_id = handle_url.rstrip("/").rsplit("/", 1)[-1]
    if not handle_id.isdigit():
        return None
    pdf = card.select_one('a[href*="/bitstream/"]')
    pdf_url = urljoin(base_url + "/", str(pdf.get("href")) if pdf else "") if pdf else None
    info = card.select_one("div.artifact-info")
    info_text = " ".join(info.get_text(" ", strip=True).split()) if info else ""
    publication_date = _date_iso(info_text)
    snippet = card.select_one("div#fulltextresults") or card.select_one("div.abstract")
    summary = " ".join(snippet.get_text(" ", strip=True).split()) if snippet else title
    case_match = _CASE_RE.search(summary)
    result_id = f"trt2-basis-{handle_id}"
    return JurisprudenceResult(
        id=result_id,
        source="trt2_basis_jurisprudencia",
        court="TRT2",
        type="acordao_ementa",
        number=case_match.group(0) if case_match else None,
        summary=summary[:8000],
        publication_date=publication_date,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw={
            "handle_id": handle_id,
            "handle_url": handle_url,
            "title": title,
            "collection_scope": COLLECTION_SCOPE,
        },
        degree="second",
        instance="second",
        branch="labor",
        authority="TRT2",
        collection="CJSG_CURATED_BULLETIN",
        document_type="acordao_ementa",
        source_origin="trt2_basis",
        document_url=pdf_url or handle_url,
    )


def _date_iso(value: str) -> str | None:
    match = _DATE_RE.search(value)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


__all__ = ["Trt2BasisJurisprudenciaProvider"]
