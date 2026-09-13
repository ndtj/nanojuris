"""TJES CJPG (first-instance) public jurisprudence provider.

TJES exposes CJPG through the same public JSON search surface used by CJSG,
but the ``pje1g`` core is a separate first-instance collection.  This module
keeps that distinction explicit and never treats process consultation as
jurisprudence.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from urllib.parse import urlsplit

import requests

from nanojuris.canonical import normalize_date
from nanojuris.config import NanoJurisConfig, configure_requests_session
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
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

TJES_CJPG_CORE = "pje1g"
TJES_CJPG_ENDPOINT = "/search"
TJES_CJPG_MAX_PAGE_SIZE = 20


class TjesCjpgProvider(JurisprudenceProvider):
    """Provider for TJES first-instance jurisprudence (CJPG)."""

    name = "tjes_cjpg"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlsplit(self.config.tjes_jurisprudencia_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=4_000_000,
                max_retries=0,
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

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/api"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_cjpg_scope(query, authority="TJES", source_label="TJES/CJPG")
        term = query.text or query.exact_phrase or query.number
        if not term:
            raise ValueError("TJES CJPG search requires text, exact_phrase or number")
        page_size = _page_size(query.page_size)
        params = build_tjes_cjpg_params(query, page_size=page_size)
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
                "core": TJES_CJPG_CORE,
                "filters": {
                    "rapporteur": query.rapporteur,
                    "updated_from": query.updated_from,
                    "updated_to": query.updated_to,
                    "order_by": query.order_by,
                },
            },
            source_url=source_url,
            limitations=[
                "CJPG usa exclusivamente o core publico pje1g e nao representa CJSG.",
                "O backend observado retorna inteiro teor textual inline, sem ementa separada.",
                "O limite conservador de 20 itens por pagina segue o contrato observado; "
                "valores maiores sao reduzidos localmente.",
                "A exposicao federada usa somente o contrato CJPG comprovado e "
                "preserva limites e falhas no SourceTrace.",
            ],
            **self._last_http_metadata,
        )
        page = parse_tjes_cjpg_response(data, query=query, trace=trace, page_size=page_size)
        self._results.update({result.id: result for result in page.results})
        return page

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        result = self._results.get(precedent_id)
        if result is None:
            raise ValueError("TJES CJPG precedent_id must be observed in the current search page")
        document = tjes_cjpg_result_to_document(result)
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
            raise ValueError("TJES CJPG document_id must be observed in the current search page")
        return tjes_cjpg_result_to_document(result)

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJES CJPG Jurisprudencia (1o grau)",
            source_url=self.api_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range", "pagination"],
            document_types=["decisao_1g", "sentenca"],
            content_formats=["json", "text", "html"],
            canonical_records=["CanonicalDecision"],
            semantic_discriminator="collection=first_degree;core=pje1g",
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "subject",
                "rapporteur",
                "judging_body",
                "origin_county",
                "judgment_date",
                "summary",
                "full_text",
                "source_id",
                "source_trace",
                "document_url",
                "core",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=["GET /api/search?core=pje1g"],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            opt_in_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            supports_live_tests=True,
            pagination_mode="offset",
            max_remote_page_size=TJES_CJPG_MAX_PAGE_SIZE,
            completeness_contract="reported_total_and_page_window",
            full_text_access="inline",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "rapporteur",
                "updated_from",
                "updated_to",
                "order_by",
            ],
            unsupported_filters=[
                "types",
                "published_from",
                "published_to",
                "source_origin",
                "fetch_details",
                "courts",
                "all_words",
                "any_words",
                "without_words",
                "case_class",
                "judging_body",
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
                "source_origins",
                "decision_type",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "native",
                "number": "translated",
                "rapporteur": "native",
                "updated_from": "translated",
                "updated_to": "translated",
                "order_by": "native",
                "types": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "source_origin": "unsupported",
                "fetch_details": "unsupported",
                "courts": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
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
                "source_origins": "unsupported",
                "decision_type": "unsupported",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
            },
            ordering_modes=["source_default", "custom_expression"],
            detail_modes=["inline_full_text"],
            limitations=[
                "A rota publica e um endpoint JSON Solr/Elasticsearch sujeito a schema drift.",
                "A data observada e dt_juntada; ela e registrada como judgment_date sem inventar "
                "data de publicacao.",
                "O total remoto e autoritativo somente quando o campo total vier no JSON.",
                "O provider nao contorna CAPTCHA, WAF, login ou rate limit.",
            ],
            responsible_use=[
                "Usar termos especificos e page_size moderado.",
                "Respeitar rate_limit_interval e limites da fonte oficial.",
                "Manter CJPG separado de CJSG e de consulta processual.",
                "Tratar bloqueio, timeout e schema drift como outcomes observaveis.",
            ],
        )

    def _request_json(self, params: dict[str, Any]) -> tuple[dict[str, Any], str]:
        url = f"{self.api_url}{TJES_CJPG_ENDPOINT}"
        request = TransportRequest(
            source=self.name,
            operation="cjpg_search",
            method="GET",
            url=url,
            params=params,
            headers={"Accept": "application/json"},
            idempotent=True,
        )
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJES CJPG request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJES CJPG transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJES CJPG transport returned no HTTP status")
        content = response.body
        response_url = str(response.final_url or url)
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": response_url,
            "content_type": response.content_type,
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": "ok" if status_code < 400 else "error",
        }
        if status_code == 429:
            raise RateLimitDetectedError("TJES CJPG returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError("TJES CJPG requires access validation")
        if status_code in {400, 422}:
            raise QueryRejectedError(f"TJES CJPG rejected query with HTTP {status_code}")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJES CJPG returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(f"TJES CJPG rejected request with HTTP {status_code}")
        try:
            data = json.loads(content.decode("utf-8", errors="replace"))
        except (TypeError, ValueError) as exc:
            raise ParserContractChangedError("TJES CJPG response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJES CJPG JSON root is not an object")
        return data, response_url


def tjes_cjpg_result_to_document(result: JurisprudenceResult) -> CanonicalDocument:
    """Convert an observed TJES/CJPG inline record into a canonical document."""

    text = result.full_text or result.summary or ""
    content = text.encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    status = ExtractionStatus.COMPLETE if text.strip() else ExtractionStatus.EMPTY
    return CanonicalDocument(
        id=result.id,
        source=result.source,
        document_type=result.document_type or result.type,
        content_type="text/plain",
        title=f"TJES/CJPG {result.number or result.id}",
        text=text or None,
        url=result.document_url,
        sha256=digest,
        byte_size=len(content),
        retrieved_at=result.source_trace.retrieved_at if result.source_trace else None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=status,
        source_trace=result.source_trace,
        extraction_trace=ExtractionTrace(
            parser="tjes_cjpg.inline_result",
            parser_version="1",
            status=status,
            access_status=AccessStatus.PUBLIC,
            content_sha256=digest,
            content_bytes=len(content),
        ),
        raw_metadata=dict(result.raw),
    )


def _validate_cjpg_scope(query: JurisprudenceQuery, *, authority: str, source_label: str) -> None:
    """Reject cross-authority or second-degree refinements on the CJPG route."""

    aliases = {"first", "primeiro", "primeiro_grau", "1", "1o", "1º"}
    degree = str(query.degree or "").strip().casefold()
    if degree and degree not in aliases:
        raise QueryRejectedError(f"{source_label} only supports degree=first")
    instance = str(query.instance or "").strip().casefold()
    if instance and instance not in aliases:
        raise QueryRejectedError(f"{source_label} only supports instance=first")
    branch = str(query.branch or "").strip().casefold()
    if branch and branch not in {"state", "estadual"}:
        raise QueryRejectedError(f"{source_label} only supports branch=state")
    requested_authority = str(query.authority or "").strip().casefold()
    if requested_authority and requested_authority != authority.casefold():
        raise QueryRejectedError(f"{source_label} cannot query authority={query.authority!r}")
    collection = str(query.collection or "").strip().casefold()
    if collection and collection not in {"cjpg", "first_degree", "jurisprudencia"}:
        raise QueryRejectedError(f"{source_label} only supports the CJPG collection")


def build_tjes_cjpg_params(
    query: JurisprudenceQuery, *, page_size: int | None = None
) -> dict[str, Any]:
    """Build the observed public TJES first-instance query parameters."""

    term = query.text or query.exact_phrase or query.number
    params: dict[str, Any] = {
        "core": TJES_CJPG_CORE,
        "q": term or "*",
        "page": max(query.page, 1),
        "per_page": _page_size(page_size or query.page_size),
    }
    if query.exact_phrase:
        params["exact_match"] = "true"
    if query.rapporteur:
        params["magistrado"] = query.rapporteur
    if query.updated_from:
        params["dataIni"] = query.updated_from
    if query.updated_to:
        params["dataFim"] = query.updated_to
    if query.order_by and query.order_by.lower() not in {"text", "relevance"}:
        params["sort"] = query.order_by
    return params


def parse_tjes_cjpg_response(
    data: dict[str, Any],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    page_size: int | None = None,
) -> SearchPage:
    """Parse one TJES ``pje1g`` JSON page into canonical result envelopes."""

    docs = data.get("docs")
    if not isinstance(docs, list):
        raise ParserContractChangedError("TJES CJPG response missing docs list")
    core_used = _first_text(data.get("core_used"))
    if core_used and core_used != TJES_CJPG_CORE:
        raise ParserContractChangedError(
            f"TJES CJPG response returned unexpected core {core_used!r}"
        )
    if any(not isinstance(doc, dict) for doc in docs):
        raise ParserContractChangedError("TJES CJPG docs contain a non-object item")
    reported_total = _as_int(data.get("total"))
    if data.get("total") is not None and reported_total is None:
        raise ParserContractChangedError("TJES CJPG response has an invalid total")
    if reported_total is not None and reported_total < 0:
        raise ParserContractChangedError("TJES CJPG response has a negative total")
    effective_size = _page_size(page_size or query.page_size)
    raw_page = data.get("page")
    raw_per_page = data.get("per_page")
    remote_page = _as_int(raw_page, default=query.page)
    remote_per_page = _as_int(raw_per_page, default=effective_size)
    if raw_page is not None and _as_int(raw_page) is None:
        raise ParserContractChangedError("TJES CJPG response has an invalid page")
    if raw_per_page is not None and _as_int(raw_per_page) is None:
        raise ParserContractChangedError("TJES CJPG response has an invalid per_page")
    if remote_page is None or remote_page < 1:
        raise ParserContractChangedError("TJES CJPG response has an invalid page")
    if remote_per_page is None or remote_per_page < 1:
        raise ParserContractChangedError("TJES CJPG response has an invalid per_page")
    results = [_doc_to_result(doc, trace=trace) for doc in docs]
    if docs and not results:
        raise ParserContractChangedError("TJES CJPG docs contain no valid objects")
    start = ((remote_page - 1) * remote_per_page) + 1 if results else 0
    complete, reason = page_completeness(
        reported_total=reported_total,
        start=start,
        returned=len(results),
        total_is_authoritative=reported_total is not None,
    )
    return SearchPage(
        source="tjes_cjpg",
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
            "core": TJES_CJPG_CORE,
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
        raise ParserContractChangedError("TJES CJPG document has no stable id")
    case_number = _first_text(doc.get("nr_processo"))
    full_text_raw = _first_text(doc.get("inteiro_teor"))
    full_text = _clean_text(full_text_raw)
    ementa = _clean_text(_first_text(doc.get("ementa")))
    summary = ementa or _summary_from_text(full_text)
    decision_type = _first_text(doc.get("tipo_decisao"), doc.get("tipo")) or "decisao_1g"
    # Keep every source field for auditability and forward compatibility, then
    # append the normalized interpretation without discarding unknown fields.
    raw = {
        **doc,
        "source_id": "tjes_cjpg",
        "core": TJES_CJPG_CORE,
        "case_class": doc.get("classe_judicial"),
        "subject": doc.get("assunto_principal"),
        "judging_body": doc.get("orgao_julgador"),
        "origin_county": doc.get("comarca"),
        "judgment_date": normalize_date(doc.get("dt_juntada")),
        "summary_source": "ementa" if ementa else "inteiro_teor_prefix",
        "full_text": full_text or None,
    }
    return JurisprudenceResult(
        id=f"tjes-cjpg-{external_id}",
        source="tjes_cjpg",
        court="TJES",
        type=decision_type,
        number=case_number,
        summary=summary or None,
        full_text=full_text or None,
        rapporteur=_first_text(doc.get("magistrado")) or None,
        judgment_date=normalize_date(doc.get("dt_juntada")),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if full_text else ExtractionStatus.PARTIAL,
        source_trace=trace,
        raw=raw,
        case_class=_first_text(doc.get("classe_judicial")) or None,
        judging_body=_first_text(doc.get("orgao_julgador")) or None,
        degree="first",
        instance="first",
        branch="state",
        authority="TJES",
        collection="CJPG",
        document_type=decision_type,
        source_origin="TJES",
    )


def _summary_from_text(text: str, *, limit: int = 1000) -> str:
    if not text:
        return ""
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
    return max(1, min(int(value or 10), TJES_CJPG_MAX_PAGE_SIZE))


def _as_int(value: Any, *, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
