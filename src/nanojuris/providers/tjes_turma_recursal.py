"""TJES Turma Recursal jurisprudence provider.

The TJES public search API exposes the legacy ``turma_recursal_legado`` core
alongside the first- and second-degree cores.  It is a separate collection:
it must not be counted as CJPG or CJSG.  The bounded public contract is
enabled for local and federated runtime use; release/deployment remains a
separate operation.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import requests

from nanojuris.canonical import normalize_date
from nanojuris.config import NanoJurisConfig
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
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus

TJES_TURMA_RECURSAL_CORE = "turma_recursal_legado"
TJES_TURMA_RECURSAL_ENDPOINT = "/api/search"
TJES_TURMA_RECURSAL_MAX_PAGE_SIZE = 20


class TjesTurmaRecursalProvider(JurisprudenceProvider):
    """Provider for the public TJES Turma Recursal collection."""

    name = "tjes_turma_recursal"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = session or requests.Session()
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
        self._inline_documents: dict[str, tuple[str, SourceTrace]] = {}

    @property
    def base_url(self) -> str:
        return self.config.tjes_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        term = query.text or query.exact_phrase or query.number
        if not term:
            raise ValueError("TJES Turma Recursal search requires text, exact_phrase or number")
        page_size = _page_size(query.page_size)
        params = build_tjes_turma_recursal_params(query, page_size=page_size)
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
                "core": TJES_TURMA_RECURSAL_CORE,
            },
            source_url=source_url,
            limitations=[
                "A collection turma_recursal_legado e separada de CJPG e CJSG.",
                "O retorno observado entrega o inteiro teor no campo cont_ementa.",
                "A promocao cobre apenas o runtime local/federado; release e deploy "
                "ficam fora do escopo.",
            ],
            **self._last_http_metadata,
        )
        page = parse_tjes_turma_recursal_response(
            data, query=query, trace=trace, page_size=page_size
        )
        for result in page.results:
            if result.full_text:
                entry = (result.full_text, trace)
                self._inline_documents[result.id] = entry
                self._inline_documents[result.id.removeprefix("tjes-turma-recursal-")] = entry
        return page

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
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
            raw=document.raw_metadata,
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        try:
            text, trace = self._inline_documents[document_id]
        except KeyError as exc:
            raise SourceUnavailableError(
                "TJES Turma Recursal inline document is available only after an observed search"
            ) from exc
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="acordao",
            content=text.encode("utf-8"),
            content_type="text/plain",
            title="TJES Turma Recursal documento inline",
            url=trace.source_url,
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"inline": True, "collection": "TURMA_RECURSAL"},
            parser=f"{self.name}.inline_document",
            parser_version="1",
            text_override=text,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJES Jurisprudencia/Turma Recursal",
            source_url=f"{self.base_url}{TJES_TURMA_RECURSAL_ENDPOINT}",
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "pagination"],
            document_types=["acordao", "recurso_inominado"],
            content_formats=["json", "text"],
            canonical_records=["CanonicalDecision"],
            semantic_discriminator=("collection=turma_recursal;core=turma_recursal_legado"),
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
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
            endpoints=["GET /api/search?core=turma_recursal_legado"],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            opt_in_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            supports_live_tests=True,
            pagination_mode="offset",
            max_remote_page_size=TJES_TURMA_RECURSAL_MAX_PAGE_SIZE,
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
                "degree": "validated_scope",
                "instance": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
            },
            ordering_modes=["source_default"],
            detail_modes=["inline_full_text"],
            limitations=[
                "A API publica e um contrato JSON sujeito a schema drift e limites da fonte.",
                "O total remoto e autoritativo somente quando inteiro e nao negativo.",
                "O provider nao contorna CAPTCHA, WAF, login ou rate limit.",
            ],
            responsible_use=[
                "Usar termos especificos e page_size moderado.",
                "Respeitar rate_limit_interval e limites publicados pelo TJES.",
                "Manter Turma Recursal separada das colecoes CJPG e CJSG.",
                "Tratar bloqueio, timeout e schema drift como outcomes observaveis.",
            ],
        )

    def _request_json(self, params: dict[str, Any]) -> tuple[dict[str, Any], str]:
        url = f"{self.base_url}{TJES_TURMA_RECURSAL_ENDPOINT}"
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
            raise SourceUnavailableError("TJES Turma Recursal transport unavailable")
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJES Turma Recursal returned no HTTP status")
        if status_code == 429:
            raise RateLimitDetectedError("TJES Turma Recursal returned HTTP 429")
        if status_code in {401, 403}:
            raise AccessControlRequiredError("TJES Turma Recursal requires access validation")
        if status_code in {400, 422}:
            raise QueryRejectedError(f"TJES Turma Recursal rejected query with HTTP {status_code}")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJES Turma Recursal returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(
                f"TJES Turma Recursal rejected request with HTTP {status_code}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJES Turma Recursal response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJES Turma Recursal JSON root is not an object")
        return data, response_url


def build_tjes_turma_recursal_params(
    query: JurisprudenceQuery, *, page_size: int | None = None
) -> dict[str, Any]:
    """Build the observed public TJES Turma Recursal query parameters."""

    term = query.text or query.exact_phrase or query.number
    return {
        "core": TJES_TURMA_RECURSAL_CORE,
        "q": term or "*",
        "page": max(query.page, 1),
        "per_page": _page_size(page_size or query.page_size),
    }


def parse_tjes_turma_recursal_response(
    data: dict[str, Any],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    page_size: int | None = None,
) -> SearchPage:
    """Parse one ``turma_recursal_legado`` JSON page."""

    docs = data.get("docs")
    if not isinstance(docs, list):
        raise ParserContractChangedError("TJES Turma Recursal response missing docs list")
    core_used = _first_text(data.get("core_used"))
    if core_used and core_used != TJES_TURMA_RECURSAL_CORE:
        raise ParserContractChangedError(
            f"TJES Turma Recursal returned unexpected core {core_used!r}"
        )
    if any(not isinstance(doc, dict) for doc in docs):
        raise ParserContractChangedError("TJES Turma Recursal docs contain a non-object item")
    reported_total = _as_int(data.get("total"))
    if data.get("total") is not None and reported_total is None:
        raise ParserContractChangedError("TJES Turma Recursal response has an invalid total")
    if reported_total is not None and reported_total < 0:
        raise ParserContractChangedError("TJES Turma Recursal response has a negative total")
    effective_size = _page_size(page_size or query.page_size)
    remote_page = _as_int(data.get("page"), default=query.page)
    remote_per_page = _as_int(data.get("per_page"), default=effective_size)
    if remote_page is None or remote_page < 1:
        raise ParserContractChangedError("TJES Turma Recursal response has an invalid page")
    if (
        remote_per_page is None
        or remote_per_page < 1
        or remote_per_page > TJES_TURMA_RECURSAL_MAX_PAGE_SIZE
    ):
        raise ParserContractChangedError("TJES Turma Recursal response has an invalid per_page")
    results = [_doc_to_result(doc, trace=trace) for doc in docs]
    start = ((remote_page - 1) * remote_per_page) + 1 if results else 0
    complete, reason = page_completeness(
        reported_total=reported_total,
        start=start,
        returned=len(results),
        total_is_authoritative=reported_total is not None,
    )
    return SearchPage(
        source="tjes_turma_recursal",
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
            "core": TJES_TURMA_RECURSAL_CORE,
            "page": str(remote_page),
            "per_page": str(remote_per_page),
        },
        total_known=reported_total is not None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY,
    )


def _doc_to_result(doc: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    external_id = _first_text(doc.get("id"), doc.get("codigo_recurso"), doc.get("num_processo"))
    if not external_id:
        raise ParserContractChangedError("TJES Turma Recursal document has no stable id")
    case_number = _first_text(doc.get("num_processo")) or None
    full_text = _clean_text(_first_text(doc.get("cont_ementa"))) or None
    summary = _summary_from_text(full_text or "") or None
    judgment_date = normalize_date(_first_text(doc.get("data_julgamento")))
    decision_type = "acordao"
    raw = {
        **doc,
        "source_id": "tjes_turma_recursal",
        "core": TJES_TURMA_RECURSAL_CORE,
        "case_class": doc.get("classe_processo"),
        "judging_body": doc.get("orgao_julgador"),
        "judgment_date": judgment_date,
        "summary_source": "cont_ementa_prefix",
        "full_text": full_text,
    }
    return JurisprudenceResult(
        id=f"tjes-turma-recursal-{external_id}",
        source="tjes_turma_recursal",
        court="TJES",
        type=decision_type,
        number=case_number,
        summary=summary,
        full_text=full_text,
        rapporteur=_first_text(doc.get("nome_juiz")) or None,
        judgment_date=judgment_date,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if full_text else ExtractionStatus.PARTIAL,
        source_trace=trace,
        raw=raw,
        case_class=_first_text(doc.get("classe_processo")) or None,
        judging_body=_first_text(doc.get("orgao_julgador")) or None,
        degree="specialized",
        instance="turma_recursal",
        branch="state",
        authority="TJES",
        collection="TURMA_RECURSAL",
        document_type=decision_type,
        source_origin="TJES",
    )


def _summary_from_text(text: str, *, limit: int = 1000) -> str:
    normalized = _clean_text(text)
    return normalized[:limit].rstrip() + ("..." if len(normalized) > limit else "")


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
    return max(1, min(int(value or 10), TJES_TURMA_RECURSAL_MAX_PAGE_SIZE))


def _as_int(value: Any, *, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


__all__ = [
    "TJES_TURMA_RECURSAL_CORE",
    "TJES_TURMA_RECURSAL_ENDPOINT",
    "TJES_TURMA_RECURSAL_MAX_PAGE_SIZE",
    "TjesTurmaRecursalProvider",
    "build_tjes_turma_recursal_params",
    "parse_tjes_turma_recursal_response",
]
