"""TJMA public Informativos de Jurisprudência provider.

The TJMA publishes a curated monthly collection of jurisprudence bulletins on
an official hot-site page.  This adapter intentionally models the collection
as curated context, not as a complete CJSG repository.  Search discovers the
official PDF editions; the PDF is fetched only through ``get_document`` so a
normal federated query does not download a multi-megabyte bulletin.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

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
    ExtractionStatus,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import (
    SharedHttpClient,
    TransportPolicy,
    TransportRequest,
    TransportStatus,
)

_EDITION_RE = re.compile(r"(?P<year>20\d{2})[_-](?P<month>0[1-9]|1[0-2])")
_PDF_RE = re.compile(r"\.pdf(?:$|[?#])", re.IGNORECASE)
_ACCESS_MARKERS = (
    "access denied",
    "acesso negado",
    "verifique que voce nao e um robo",
    "challenge-error-text",
    "cf-chl-",
)
_SUPPORTED_TYPES = {"informativo", "informativo_jurisprudencia", "curated_jurisprudence"}


class TjmaInformativosProvider(JurisprudenceProvider):
    """Expose TJMA's official curated jurisprudence bulletins."""

    name = "tjma_informativos"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_http_metadata: dict[str, Any] = {}
        self._document_urls: dict[str, str] = {}
        listing_host = urlparse(self.config.tjma_informativos_url).hostname or ""
        self._document_policy = TransportPolicy(
            allowed_hosts=(listing_host, "novogerenciador.tjma.jus.br"),
            timeout_seconds=self.config.timeout,
            max_bytes=12_000_000,
            max_redirects=3,
            max_retries=2,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self._listing_policy = TransportPolicy(
            allowed_hosts=(listing_host,),
            timeout_seconds=self.config.timeout,
            max_bytes=8_000_000,
            max_redirects=3,
            max_retries=0,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self._transport = SharedHttpClient(self._listing_policy, session=self.session)

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        html, final_url = self._request_listing()
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /midia/pje/pagina/hotsite/509874",
            query={"page": query.page, "page_size": query.page_size},
            source_url=final_url,
            limitations=[
                "Coleção curada de informativos; não representa o acervo integral "
                "de acórdãos do TJMA.",
                "O texto integral do boletim só é baixado quando get_document é solicitado.",
                "A página oficial não publica um total histórico autoritativo de edições.",
            ],
            **self._last_http_metadata,
        )
        page = parse_tjma_informativos(
            html,
            query=query,
            trace=trace,
            base_url=self.config.tjma_informativos_url,
        )
        for result in page.results:
            document_url = str(result.document_url or "")
            if document_url:
                self._document_urls[result.id] = document_url
        return page

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document_url = self._document_urls.get(precedent_id)
        if not document_url:
            return DecisionBundle(
                precedent_id=precedent_id,
                source=self.name,
                texts=[],
                raw={
                    "message": (
                        "TJMA Informativos exposes curated bulletin editions. "
                        "Run search first and request get_document for the official PDF."
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
        """Fetch an observed official bulletin PDF through shared transport."""

        document_url = (
            document_id
            if document_id.startswith("https://")
            else self._document_urls.get(document_id)
        )
        if not document_url:
            raise ValueError(
                "TJMA Informativos document_id must be an observed result id or HTTPS URL"
            )
        if not self._document_policy.allows(document_url):
            raise ValueError("TJMA Informativos document URL is outside the configured allowlist")
        reference = DocumentReference(
            id=document_id,
            source=self.name,
            url=document_url,
            document_type="informativo_jurisprudencia",
            expected_content_types=("application/pdf",),
        )
        return fetch_document_reference(
            reference,
            policy=self._document_policy,
            session=self.session,
            title=f"TJMA Informativo {document_id}",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJMA Informativos de Jurisprudência",
            source_url=self.config.tjma_informativos_url,
            category="curated_jurisprudence",
            search_modes=["curated_catalog", "edition_metadata"],
            document_types=["informativo_jurisprudencia"],
            content_formats=["html", "pdf"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator="official curated TJMA bulletin edition",
            extracted_fields=[
                "source_record_id",
                "edition_period",
                "title",
                "publication_date",
                "document_url",
                "authority",
                "branch",
                "degree",
                "instance",
                "collection",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /midia/pje/pagina/hotsite/509874",
                "GET novogerenciador.tjma.jus.br/*.pdf",
            ],
            supports_full_text=True,
            supports_catalog=True,
            supports_suggestions=False,
            supports_live_tests=True,
            supports_cli=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            pagination_mode="local_window",
            completeness_contract="observed_public_edition_window",
            full_text_access="document_link",
            supported_filters=["page", "authority", "branch", "degree", "instance", "collection"],
            unsupported_filters=[
                "courts",
                "types",
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "updated_from",
                "updated_to",
                "party_name",
                "party_document",
                "lawyer_name",
                "oab",
                "precatory_number",
                "police_document",
                "cda",
                "source_origin",
                "source_origins",
                "legal_area",
                "decision_type",
            ],
            filter_semantics={
                "page": "local_postfilter",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "text": "unsupported",
                "number": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "rapporteur": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
                "fetch_details": "unsupported",
                **{
                    name: "unsupported"
                    for name in (
                        "courts",
                        "types",
                        "all_words",
                        "any_words",
                        "without_words",
                        "exact_phrase",
                        "updated_from",
                        "updated_to",
                        "party_name",
                        "party_document",
                        "lawyer_name",
                        "oab",
                        "precatory_number",
                        "police_document",
                        "cda",
                        "source_origin",
                        "source_origins",
                        "legal_area",
                        "decision_type",
                    )
                },
            },
            limitations=[
                "Informativos são uma seleção editorial de decisões relevantes, "
                "não uma coleção geral completa.",
                "A pesquisa da página localiza edições; o texto do PDF é obtido sob demanda.",
                "A fonte não informa um total histórico autoritativo nem filtros "
                "internos de assunto.",
            ],
            responsible_use=[
                "Citar a edição e o PDF oficial ao usar o conteúdo.",
                "Não tratar o informativo como acórdão individual ou precedente vinculante.",
                "Manter o provider opt-in para evitar download de PDFs em toda busca federada.",
            ],
        )

    def _request_listing(self) -> tuple[str, str]:
        url = self.config.tjma_informativos_url
        try:
            response = self._transport.request(
                TransportRequest(
                    source=self.name,
                    operation="listing",
                    method="GET",
                    url=url,
                    headers={"Accept": "text/html,application/xhtml+xml"},
                )
            )
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(f"TJMA Informativos request failed: {exc}") from exc
        text = response.text
        final_url = response.final_url or response.url or url
        status = int(response.status_code or 0)
        self._last_http_metadata = {
            "http_status": status,
            "final_url": final_url,
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok"
            if response.status is TransportStatus.COMPLETE and 200 <= status < 400
            else response.status.value,
        }
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJMA Informativos request failed: {response.status.value}"
            )
        if status in {401, 403} or _looks_like_access_control(text):
            raise AccessControlRequiredError("TJMA Informativos returned access-control response")
        if status == 429:
            raise RateLimitDetectedError("TJMA Informativos returned HTTP 429")
        if status >= 500 or status >= 400:
            raise SourceUnavailableError(f"TJMA Informativos returned HTTP {status}")
        if not text.strip():
            raise ParserContractChangedError("TJMA Informativos listing is empty")
        return text, final_url


def parse_tjma_informativos(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    """Parse official PDF edition links into curated result records."""

    soup = BeautifulSoup(html, "html.parser")
    by_url: dict[str, tuple[str, str, str]] = {}
    for anchor in soup.select("a[href]"):
        href = str(anchor.get("href") or "").strip()
        if not href or not _PDF_RE.search(href):
            continue
        url = urljoin(base_url, href)
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "novogerenciador.tjma.jus.br":
            continue
        match = _EDITION_RE.search(url) or _EDITION_RE.search(anchor.get_text(" ", strip=True))
        if match is None:
            continue
        period = f"{match.group('year')}-{match.group('month')}"
        label = _normalize_text(anchor.get_text(" ", strip=True)) or f"Informativo TJMA {period}"
        # Keep the canonical PDF only; the editable RTF is intentionally out of scope.
        if "edit" in label.casefold() or url.casefold().endswith(".rtf"):
            continue
        by_url[url] = (period, label, url)
    if not by_url:
        visible = _normalize_text(soup.get_text(" ", strip=True)).casefold()
        if any(marker in visible for marker in ("nenhum", "sem resultado", "não encontrado")):
            return _empty_page(query, trace, "A página oficial informou ausência de edições.")
        raise ParserContractChangedError("TJMA Informativos PDF edition links not found")

    rows = sorted(by_url.values(), key=lambda row: row[0], reverse=True)
    rows = _apply_scope_filters(rows, query)
    if not rows:
        return _empty_page(query, trace, "Os filtros de escopo não correspondem à coleção TJMA.")
    start_index = (query.page - 1) * query.page_size
    window = rows[start_index : start_index + query.page_size]
    results: list[JurisprudenceResult] = []
    for period, label, url in window:
        stable = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
        result_id = f"tjma-informativo-{period}-{stable}"
        results.append(
            JurisprudenceResult(
                id=result_id,
                source="tjma_informativos",
                court="TJMA",
                type="informativo_jurisprudencia",
                summary=label,
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.COMPLETE,
                source_trace=trace,
                degree="second",
                instance="second",
                branch="state",
                authority="TJMA",
                collection="INFORMATIVO",
                document_type="informativo_jurisprudencia",
                # The official listing exposes only year-month precision.  It
                # is preserved as a partial publication date, never expanded
                # to an invented day.
                publication_date=period,
                source_origin="TJMA official jurisprudence hot-site",
                document_url=url,
                raw={
                    "source_record_id": result_id,
                    "edition_period": period,
                    "title": label,
                    "document_url": url,
                    "curated_source": True,
                    "full_text_on_demand": True,
                    "scope_note": "curated bulletin, not complete CJSG corpus",
                },
                field_provenance={
                    "source_record_id": {
                        "value": result_id,
                        "method": "official_pdf_url_fingerprint",
                    },
                    "authority": {"source": "official_listing", "confidence": "high"},
                    "degree": {"source": "bulletin_scope", "confidence": "medium"},
                    "collection": {"source": "official_listing", "confidence": "high"},
                    "publication_date": {
                        "value": period,
                        "granularity": "month",
                        "source": "edition_url_or_label",
                    },
                    "document_url": {"source": "official_listing", "confidence": "high"},
                },
            )
        )
    complete, reason = page_completeness(
        reported_total=len(rows),
        start=start_index + 1 if window else 0,
        returned=len(window),
        total_is_authoritative=False,
    )
    return SearchPage(
        source="tjma_informativos",
        total=len(rows),
        start=start_index + 1 if window else 0,
        end=start_index + len(window) if window else 0,
        page=query.page,
        page_size=query.page_size,
        results=results,
        source_trace=trace,
        pagination_mode="local_window",
        is_complete=complete,
        completeness_reason=reason,
        total_known=False,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        filters_applied={
            "authority": "validated_scope",
            "branch": "validated_scope",
            "degree": "validated_scope",
            "instance": "validated_scope",
            "collection": "validated_scope",
            "page": "local_postfilter",
            "text": "unsupported_document_body_not_scanned",
            "number": "unsupported",
        },
    )


def _apply_scope_filters(
    rows: list[tuple[str, str, str]], query: JurisprudenceQuery
) -> list[tuple[str, str, str]]:
    """Apply only filters that are proven from listing scope metadata."""

    if query.types and not any(str(value).casefold() in _SUPPORTED_TYPES for value in query.types):
        return []
    if query.collection and query.collection.casefold() not in {"informativo", "informatÃ­vo"}:
        return []
    if query.document_type and query.document_type.casefold() != "informativo_jurisprudencia":
        return []
    if query.authority and query.authority.casefold() not in {"tjma", "maranhao"}:
        return []
    if query.branch and query.branch.casefold() not in {"state", "estadual"}:
        return []
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2"}:
        return []
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2"}:
        return []
    return rows


def _empty_page(query: JurisprudenceQuery, trace: SourceTrace, reason: str) -> SearchPage:
    return SearchPage(
        source="tjma_informativos",
        total=0,
        start=0,
        end=0,
        page=query.page,
        page_size=query.page_size,
        results=[],
        source_trace=trace,
        pagination_mode="local_window",
        is_complete=True,
        completeness_reason=reason,
        total_known=True,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.EMPTY,
        filters_applied={"scope": "validated_scope", "page": "local_postfilter"},
    )


def _normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _looks_like_access_control(text: str) -> bool:
    normalized = _normalize_text(BeautifulSoup(text, "html.parser").get_text(" ")).casefold()
    return any(marker in normalized for marker in _ACCESS_MARKERS)


__all__ = ["TjmaInformativosProvider", "parse_tjma_informativos"]
