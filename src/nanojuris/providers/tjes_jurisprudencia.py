"""TJES/CJSG public jurisprudence provider (second-degree ``pje2g`` core)."""

from __future__ import annotations

import hashlib
from html import unescape
from typing import Any

import requests
from bs4 import BeautifulSoup

from nanojuris.canonical import normalize_date
from nanojuris.config import NanoJurisConfig
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
    ExtractionTrace,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus

TJES_CJSG_CORE = "pje2g"
TJES_CJSG_ENDPOINT = "/api/search"
TJES_CJSG_MAX_PAGE_SIZE = 20


class TjesJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for TJES second-degree jurisprudence (CJSG)."""

    name = "tjes_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = session or requests.Session()
        from urllib.parse import urlparse

        host = urlparse(self.config.tjes_jurisprudencia_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_retries=2,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_http_metadata: dict[str, Any] = {}
        self._results: dict[str, JurisprudenceResult] = {}

    @property
    def base_url(self) -> str:
        return self.config.tjes_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        term = query.text or query.exact_phrase or query.number
        if not term:
            raise ValueError("TJES CJSG search requires text, exact_phrase or number")
        page_size = _page_size(query.page_size)
        params = build_tjes_cjsg_params(query, page_size=page_size)
        data, source_url = self._request_json(params)
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /api/search",
            query={
                "text": query.text,
                "exact_phrase": query.exact_phrase,
                "number": query.number,
                "page": query.page,
                "page_size": page_size,
                "core": TJES_CJSG_CORE,
            },
            source_url=source_url,
            limitations=[
                "O core publico pje2g representa segundo grau; nao representa CJPG/pje1g.",
                "O retorno observado entrega ementa e acordao inline; nao ha detalhe separado.",
                "Cores pje2g_mono, legado e turma recursal permanecem fora deste adapter.",
                "A federacao usa o contrato publico comprovado; limites e falhas "
                "permanecem observaveis no SourceTrace.",
            ],
            **self._last_http_metadata,
        )
        page = parse_tjes_cjsg_response(data, query=query, trace=trace, page_size=page_size)
        self._results.update({result.id: result for result in page.results})
        return page

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        result = self._results.get(precedent_id)
        if result is None:
            raise ValueError("TJES precedent_id must be observed in the current search page")
        document = tjes_result_to_document(result)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            rapporteur=result.rapporteur,
            texts=[{"type": result.document_type or result.type, "text": document.text or ""}],
            source_trace=result.source_trace,
            raw={"document": document.raw_metadata},
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        result = self._results.get(document_id)
        if result is None:
            raise ValueError("TJES document_id must be observed in the current search page")
        return tjes_result_to_document(result)

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJES Jurisprudencia/CJSG (2o grau)",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "pagination"],
            document_types=["acordao", "decisao_monocratica"],
            content_formats=["json", "text", "html"],
            canonical_records=["CanonicalDecision"],
            semantic_discriminator="collection=second_degree;core=pje2g",
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "subject",
                "rapporteur",
                "judging_body",
                "summary",
                "full_text",
                "judgment_date",
                "source_trace",
                "document_url",
                "core",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=["GET /api/search?core=pje2g"],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            opt_in_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            supports_live_tests=True,
            pagination_mode="offset",
            max_remote_page_size=TJES_CJSG_MAX_PAGE_SIZE,
            completeness_contract="reported_total_and_page_window",
            full_text_access="inline",
            supported_filters=["text", "exact_phrase", "number", "page"],
            unsupported_filters=[
                "courts",
                "types",
                "rapporteur",
                "updated_from",
                "updated_to",
                "fetch_details",
                "all_words",
                "any_words",
                "without_words",
                "case_class",
                "judging_body",
                "decision_type",
                "judgment_date_from",
                "judgment_date_to",
                "lawyer_name",
                "legal_area",
                "oab",
                "party_document",
                "party_name",
                "police_document",
                "precatory_number",
                "cda",
                "source_origin",
                "source_origins",
                "published_from",
                "published_to",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "translated",
                "number": "translated",
                "page": "native",
                "courts": "unsupported",
                "types": "unsupported",
                "rapporteur": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
                "fetch_details": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "decision_type": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
                "lawyer_name": "unsupported",
                "legal_area": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "cda": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "document_type": "validated_scope",
            },
            ordering_modes=["source_default"],
            detail_modes=["inline_full_text"],
            limitations=[
                "A API publica e um contrato JSON sujeito a schema drift e limites da fonte.",
                "O total remoto e autoritativo somente quando inteiro e nao negativo.",
                "A fonte nao foi tratada como autorizacao de redistribuicao em escala.",
                "O provider nao contorna CAPTCHA, WAF, login ou rate limit.",
            ],
            responsible_use=[
                "Usar termos especificos e page_size moderado.",
                "Respeitar rate_limit_interval e os limites publicados pelo TJES.",
                "Manter CJSG separado de CJPG e de consulta processual.",
                "Tratar bloqueio, timeout e schema drift como outcomes observaveis.",
            ],
        )

    def _request_json(self, params: dict[str, Any]) -> tuple[dict[str, Any], str]:
        url = f"{self.base_url}{TJES_CJSG_ENDPOINT}"
        response = self.transport.request(
            TransportRequest(
                source=self.name,
                operation="search",
                method="GET",
                url=url,
                params=params,
                headers={"Accept": "application/json"},
                idempotent=True,
            )
        )
        response_url = response.final_url or url
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": response_url,
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": response.status.value,
        }
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError("TJES CJSG transport unavailable")
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJES CJSG returned no HTTP status")
        if status_code == 429:
            raise RateLimitDetectedError("TJES CJSG returned HTTP 429")
        if status_code in {401, 403}:
            raise AccessControlRequiredError("TJES CJSG requires access validation")
        if status_code in {400, 422}:
            raise QueryRejectedError(f"TJES CJSG rejected query with HTTP {status_code}")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJES CJSG returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(f"TJES CJSG rejected request with HTTP {status_code}")
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJES CJSG response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJES CJSG JSON root is not an object")
        return data, response_url


def tjes_result_to_document(result: JurisprudenceResult) -> CanonicalDocument:
    """Convert an observed TJES/CJSG inline record into a canonical document."""

    text = result.full_text or result.summary or ""
    content = text.encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    status = ExtractionStatus.COMPLETE if text.strip() else ExtractionStatus.EMPTY
    return CanonicalDocument(
        id=result.id,
        source=result.source,
        document_type=result.document_type or result.type,
        content_type="text/plain",
        title=f"TJES/CJSG {result.number or result.id}",
        text=text or None,
        url=result.document_url,
        sha256=digest,
        byte_size=len(content),
        retrieved_at=result.source_trace.retrieved_at if result.source_trace else None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=status,
        source_trace=result.source_trace,
        extraction_trace=ExtractionTrace(
            parser="tjes_jurisprudencia.inline_result",
            parser_version="1",
            status=status,
            access_status=AccessStatus.PUBLIC,
            content_sha256=digest,
            content_bytes=len(content),
        ),
        raw_metadata=dict(result.raw),
    )


def build_tjes_cjsg_params(
    query: JurisprudenceQuery, *, page_size: int | None = None
) -> dict[str, Any]:
    """Build the observed public TJES second-degree query parameters."""

    term = query.text or query.exact_phrase or query.number
    return {
        "core": TJES_CJSG_CORE,
        "q": term or "*",
        "page": max(query.page, 1),
        "per_page": _page_size(page_size or query.page_size),
    }


def parse_tjes_cjsg_response(
    data: dict[str, Any],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    page_size: int | None = None,
) -> SearchPage:
    """Parse one TJES ``pje2g`` JSON page into canonical result envelopes."""

    docs = data.get("docs")
    if not isinstance(docs, list):
        raise ParserContractChangedError("TJES CJSG response missing docs list")
    core_used = _first_text(data.get("core_used"))
    if core_used and core_used != TJES_CJSG_CORE:
        raise ParserContractChangedError(
            f"TJES CJSG response returned unexpected core {core_used!r}"
        )
    if any(not isinstance(doc, dict) for doc in docs):
        raise ParserContractChangedError("TJES CJSG docs contain a non-object item")
    reported_total = _as_int(data.get("total"))
    if data.get("total") is not None and reported_total is None:
        raise ParserContractChangedError("TJES CJSG response has an invalid total")
    if reported_total is not None and reported_total < 0:
        raise ParserContractChangedError("TJES CJSG response has a negative total")
    effective_size = _page_size(page_size or query.page_size)
    remote_page = _as_int(data.get("page"), default=query.page)
    remote_per_page = _as_int(data.get("per_page"), default=effective_size)
    if remote_page is None or remote_page < 1:
        raise ParserContractChangedError("TJES CJSG response has an invalid page")
    if remote_per_page is None or remote_per_page < 1 or remote_per_page > TJES_CJSG_MAX_PAGE_SIZE:
        raise ParserContractChangedError("TJES CJSG response has an invalid per_page")
    results = [_doc_to_result(doc, trace=trace) for doc in docs]
    start = ((remote_page - 1) * remote_per_page) + 1 if results else 0
    complete, reason = page_completeness(
        reported_total=reported_total,
        start=start,
        returned=len(results),
        total_is_authoritative=reported_total is not None,
    )
    return SearchPage(
        source="tjes_jurisprudencia",
        total=reported_total if reported_total is not None else len(results),
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=remote_page,
        page_size=remote_per_page,
        results=results,
        source_trace=trace,
        pagination_mode="offset",
        is_complete=complete,
        completeness_reason=reason,
        ordering=query.order_by,
        filters_applied={
            "core": TJES_CJSG_CORE,
            "page": str(remote_page),
            "per_page": str(remote_per_page),
        },
        total_known=reported_total is not None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY,
    )


def _doc_to_result(doc: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    external_id = _first_text(doc.get("id"), doc.get("id_bin"), doc.get("nr_processo"))
    if not external_id:
        raise ParserContractChangedError("TJES CJSG document has no stable id")
    case_number = _first_text(doc.get("nr_processo")) or None
    summary, summary_source = _text_with_html_fallback(
        doc.get("ementa"), doc.get("ementa_html"), plain_source="ementa"
    )
    full_text, full_text_source = _text_with_html_fallback(
        doc.get("acordao"), doc.get("acordao_html"), plain_source="acordao"
    )
    if not summary and full_text:
        summary = _summary_from_text(full_text)
        summary_source = "acordao_prefix"
    decision_type = _first_text(doc.get("tipo_decisao"), doc.get("tipo")) or "acordao"
    raw = {
        **doc,
        "source_id": "tjes_jurisprudencia",
        "core": TJES_CJSG_CORE,
        "case_class": doc.get("classe_judicial"),
        "subject": doc.get("assunto_principal"),
        "judging_body": doc.get("orgao_julgador"),
        "judgment_date": normalize_date(doc.get("dt_juntada")),
        "summary_source": summary_source,
        "full_text_source": full_text_source,
        "full_text": full_text,
    }
    return JurisprudenceResult(
        id=f"tjes-cjsg-{external_id}",
        source="tjes_jurisprudencia",
        court="TJES",
        type=decision_type,
        number=case_number,
        summary=summary,
        full_text=full_text,
        rapporteur=_first_text(doc.get("magistrado")) or None,
        judgment_date=normalize_date(doc.get("dt_juntada")),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE
        if summary or full_text
        else ExtractionStatus.PARTIAL,
        source_trace=trace,
        raw=raw,
        case_class=_first_text(doc.get("classe_judicial")) or None,
        judging_body=_first_text(doc.get("orgao_julgador")) or None,
        degree="second",
        instance="second",
        branch="state",
        authority="TJES",
        collection="CJSG",
        document_type=decision_type,
        source_origin="TJES",
    )


def _summary_from_text(text: str, *, limit: int = 1000) -> str:
    normalized = _clean_text(text)
    return normalized[:limit].rstrip() + ("..." if len(normalized) > limit else "")


def _text_with_html_fallback(
    plain_value: Any,
    html_value: Any,
    *,
    plain_source: str,
) -> tuple[str | None, str | None]:
    """Return usable text while preserving whether the source was HTML."""

    plain_text = _clean_text(_first_text(plain_value))
    if plain_text:
        return plain_text, plain_source
    html_text = _html_to_text(_first_text(html_value))
    if html_text:
        return html_text, f"{plain_source}_html"
    return None, None


def _html_to_text(value: str) -> str:
    if not value:
        return ""
    parsed = BeautifulSoup(unescape(value), "html.parser")
    return _clean_text(parsed.get_text(" ", strip=True))


def _first_text(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        if isinstance(value, list):
            value = " ".join(str(item) for item in value if item is not None)
        text = str(value).strip()
        if text:
            return text
    return ""


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), TJES_CJSG_MAX_PAGE_SIZE))


def _as_int(value: Any, *, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


__all__ = [
    "TJES_CJSG_CORE",
    "TJES_CJSG_ENDPOINT",
    "TJES_CJSG_MAX_PAGE_SIZE",
    "TjesJurisprudenciaProvider",
    "build_tjes_cjsg_params",
    "parse_tjes_cjsg_response",
]
