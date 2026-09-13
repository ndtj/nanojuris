"""TJRN public textual jurisprudence adapter."""

from __future__ import annotations

import re
from typing import Any, cast
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

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

TJRN_ENDPOINT = "/api/pesquisar"
TJRN_MAX_PAGE_SIZE = 10


class TjrnJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the TJRN public jurisprudence portal."""

    name = "tjrn_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        host = urlparse(self.config.tjrn_jurisprudencia_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_retries=2,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=session,
        )
        self._inline_documents: dict[str, tuple[str, str, SourceTrace]] = {}

    @property
    def base_url(self) -> str:
        return self.config.tjrn_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        term = query.exact_phrase or query.text or query.number
        if not term:
            raise ValueError("TJRN jurisprudence search requires text, exact_phrase or number")
        page_size = min(query.page_size, TJRN_MAX_PAGE_SIZE)
        payload = build_tjrn_payload(query, page_size=page_size)
        response = self._request(payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"POST {TJRN_ENDPOINT}",
            query={
                "text": query.text,
                "exact_phrase": query.exact_phrase,
                "number": query.number,
                "page": query.page,
                "page_size": page_size,
            },
            source_url=response.final_url or f"{self.base_url}{TJRN_ENDPOINT}",
            limitations=[
                "O endpoint publico observado recebe contexto usuario vazio; nenhuma "
                "sessao e reutilizada.",
                "A fonte retorna documentos PJe/SAJ em uma busca unificada; o sistema "
                "de origem e preservado em raw.",
                "Filtros de classe, grau, tipo e ordenacao aguardam reproducao independente.",
                "A federacao usa somente o contrato textual comprovado; filtros nao "
                "confirmados permanecem explicitamente unsupported.",
            ],
            http_status=response.status_code,
            final_url=response.final_url,
            content_type=response.content_type,
            content_sha256=response.content_sha256,
            response_bytes=response.byte_size,
            elapsed_ms=response.elapsed_ms,
            retrieval_status="ok"
            if response.status is TransportStatus.COMPLETE
            else response.status.value,
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJRN response is not valid JSON") from exc
        page = parse_tjrn_response(data, query=query, trace=trace, page_size=page_size)
        for result in page.results:
            if result.full_text:
                self._inline_documents[result.id] = (result.full_text, result.full_text, trace)
                self._inline_documents[result.id.removeprefix("tjrn-jurisprudencia-")] = (
                    result.full_text,
                    result.full_text,
                    trace,
                )
        return page

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Return text embedded in the public TJRN search response."""

        entry = self._inline_documents.get(document_id)
        if entry is None:
            raise KeyError("TJRN inline document is available only after search")
        content, text, trace = entry
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="inteiro_teor",
            content=content.encode("utf-8"),
            content_type="text/plain",
            url=trace.source_url,
            title="TJRN jurisprudência — documento inline",
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"inline": True, "document_id": document_id},
            parser=f"{self.name}.inline_document",
            parser_version="1",
            text_override=text,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        try:
            document = self.get_document(precedent_id)
        except KeyError as exc:
            raise SourceUnavailableError(
                "TJRN inline document is available only after an observed search"
            ) from exc
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

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJRN Jurisprudencia textual (portal unificado)",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "pagination"],
            document_types=["acordao", "decisao_monocratica", "sentenca"],
            content_formats=["json", "text"],
            canonical_records=["CanonicalDecision"],
            semantic_discriminator="collection=unified;court=TJRN",
            extracted_fields=[
                "id",
                "case_number",
                "decision_type",
                "case_class",
                "subject",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "updated_at",
                "summary",
                "full_text",
                "document_url",
                "system",
                "degree",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=["POST /api/pesquisar"],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            opt_in_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            supports_live_tests=True,
            pagination_mode="page",
            max_remote_page_size=TJRN_MAX_PAGE_SIZE,
            completeness_contract="hits_total_and_page_window",
            full_text_access="inline",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "page",
                "degree",
                "instance",
                "case_class",
                "judging_body",
                "source_origin",
                "decision_type",
                "judgment_date_from",
                "judgment_date_to",
            ],
            unsupported_filters=[
                "courts",
                "types",
                "rapporteur",
                "updated_from",
                "updated_to",
                "published_from",
                "published_to",
                "fetch_details",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "native",
                "number": "translated",
                "page": "native",
                "courts": "unsupported",
                "types": "unsupported",
                "rapporteur": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "fetch_details": "unsupported",
                # The public endpoint reports a mixed page.  Degree refinement
                # is therefore an explicit bounded post-filter and cannot
                # claim a complete remote total.
                "degree": "local_postfilter",
                "instance": "local_postfilter",
                "case_class": "local_postfilter",
                "judging_body": "local_postfilter",
                "source_origin": "local_postfilter",
                "decision_type": "local_postfilter",
                "judgment_date_from": "local_postfilter",
                "judgment_date_to": "local_postfilter",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "source_origins": "unsupported",
                "cda": "unsupported",
                "lawyer_name": "unsupported",
                "legal_area": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
            },
            ordering_modes=["source_default"],
            detail_modes=["inline_full_text"],
            limitations=[
                "A rota retornou HTTP 403 em uma rechecagem posterior; isso e bloqueio "
                "de acesso, nao vazio.",
                "A semantica de pagina e total deve ser revalidada quando o endpoint "
                "estiver acessivel.",
                "Nenhuma tentativa de contornar WAF, CAPTCHA, login ou rate limit e permitida.",
            ],
            responsible_use=[
                "Usar termos especificos, page_size ate 10 e intervalo entre chamadas.",
                "Manter origem (PJe/SAJ) e grau em raw sem misturar consulta processual.",
                "Usar somente a rota publica e manter os outcomes de acesso observaveis.",
            ],
        )

    def _request(self, payload: dict[str, Any]):
        request = TransportRequest(
            source=self.name,
            operation="search",
            method="POST",
            url=f"{self.base_url}{TJRN_ENDPOINT}",
            json_body=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            idempotent=False,
        )
        response = self.transport.request(request)
        if response.status in {
            TransportStatus.TIMEOUT,
            TransportStatus.TLS_ERROR,
            TransportStatus.SOURCE_UNAVAILABLE,
            TransportStatus.RESPONSE_TOO_LARGE,
            TransportStatus.CIRCUIT_OPEN,
        }:
            raise SourceUnavailableError("TJRN transport unavailable")
        if response.status_code == 429:
            raise RateLimitDetectedError("TJRN returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJRN requires access validation")
        if response.status_code in {400, 422}:
            raise QueryRejectedError(f"TJRN rejected query with HTTP {response.status_code}")
        if response.status_code is None or response.status_code >= 500:
            raise SourceUnavailableError("TJRN returned an unavailable response")
        if response.status_code >= 400:
            raise SourceUnavailableError("TJRN rejected the request")
        return response


def build_tjrn_payload(
    query: JurisprudenceQuery, *, page_size: int = TJRN_MAX_PAGE_SIZE
) -> dict[str, Any]:
    """Build only fields confirmed by the public portal contract."""

    term = query.exact_phrase or query.text or query.number
    jurisprudencia: dict[str, str] = {"ementa": term or ""}
    if query.number:
        jurisprudencia["numero_processo"] = query.number
    return {
        "jurisprudencia": jurisprudencia,
        "page": max(1, query.page),
        "usuario": {},
    }


def parse_tjrn_response(
    data: dict[str, Any],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    page_size: int,
) -> SearchPage:
    hits_container = data.get("hits")
    if not isinstance(hits_container, dict):
        raise ParserContractChangedError("TJRN response missing hits object")
    raw_hits = hits_container.get("hits")
    if not isinstance(raw_hits, list) or any(not isinstance(item, dict) for item in raw_hits):
        raise ParserContractChangedError("TJRN response missing hits.hits list")
    results = [_result_from_hit(item, trace=trace) for item in raw_hits]
    # The public endpoint accepts only the free-text/number payload.  Apply
    # canonical refinements locally when the response exposes the field, and
    # explicitly downgrade completeness because the remote total describes the
    # unfiltered mixed collection.  Never silently drop a requested field.
    local_filters = {
        name: value
        for name, value in (
            ("degree", query.degree),
            ("instance", query.instance),
            ("case_class", query.case_class),
            ("judging_body", query.judging_body),
            ("source_origin", query.source_origin),
            ("decision_type", query.decision_type),
            ("judgment_date_from", query.judgment_date_from),
            ("judgment_date_to", query.judgment_date_to),
        )
        if value
    }
    local_filter_names = set(local_filters)
    if local_filter_names:
        results = [result for result in results if _matches_local_filters(result, local_filters)]
    degree_postfiltered = bool(local_filter_names)
    total = _total_from_hits(hits_container.get("total"))
    results = results[:page_size]
    start = ((max(query.page, 1) - 1) * page_size) + 1 if results else 0
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        # The endpoint reports a mixed total when degree is refined locally;
        # retain the count but do not claim a complete filtered window.
        total_is_authoritative=not degree_postfiltered,
    )
    return SearchPage(
        source="tjrn_jurisprudencia",
        total=total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=query.page,
        page_size=page_size,
        results=results,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=reason,
        ordering="source_default",
        filters_applied={
            "text": "native",
            "page": "native",
            **{name: "local_postfilter" for name in local_filter_names},
        },
        total_known=not degree_postfiltered,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY,
    )


def _result_from_hit(hit: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    source_raw = hit.get("_source")
    if isinstance(source_raw, dict):
        source = cast(dict[str, Any], source_raw)
    else:
        fields = hit.get("fields")
        source = cast(dict[str, Any], fields if isinstance(fields, dict) else hit)
    identifier = _text(
        source.get("id_documento"), source.get("documento_id"), hit.get("_id"), source.get("id")
    )
    if not identifier:
        raise ParserContractChangedError("TJRN result is missing a stable identifier")
    # TJRN currently returns rich HTML fragments in ``ementa``/``decisao``.
    # Keep the original markup in ``raw`` but expose plain text through the
    # canonical fields; otherwise HTML tags leak into the federated reader and
    # make quality validation report a false textual hit.
    summary_raw = _text(source.get("ementa"), source.get("resumo"))
    full_text_raw = _text(
        source.get("inteiro_teor"), source.get("texto_integral"), source.get("decisao")
    )
    summary = _plain_text(summary_raw)
    full_text = _plain_text(full_text_raw)
    judgment_raw = _text(source.get("dt_julgamento"), source.get("data_julgamento"))
    publication_raw = _text(source.get("dt_publicacao"), source.get("data_publicacao"))
    # Keep every source field available to downstream audit/reconciliation. The
    # canonical fields below are additive and never replace the original keys.
    raw = dict(source)
    degree_raw = _text(source.get("grau"), source.get("instancia"))
    instance_raw = _text(source.get("instancia"), source.get("instance"))
    degree = _normalize_degree(degree_raw)
    instance = _normalize_degree(instance_raw or degree_raw)
    raw.update(
        {
            "native_id": identifier,
            "case_class": _text(source.get("classe_judicial"), source.get("classe")),
            "judging_body": _text(source.get("orgao_julgador"), source.get("orgao")),
            "degree": degree_raw,
            "instance": instance_raw,
            "system": _text(source.get("sistema"), source.get("origem")),
            "judgment_date_raw": judgment_raw,
            "publication_date_raw": publication_raw,
            "source_fields": sorted(str(key) for key in source),
        }
    )
    decision_type = _text(source.get("tipo_documento"), source.get("tipo")) or "decisao"
    case_class = _text(source.get("classe_judicial"), source.get("classe"))
    judging_body = _text(source.get("orgao_julgador"), source.get("orgao"))
    degree = _normalize_degree(degree_raw)
    instance = _normalize_degree(instance_raw or degree_raw)
    source_origin = _text(source.get("sistema"), source.get("origem"))
    return JurisprudenceResult(
        id=f"tjrn-jurisprudencia-{identifier}",
        source="tjrn_jurisprudencia",
        court="TJRN",
        type=decision_type,
        number=_text(source.get("numero_processo"), source.get("processo")),
        summary=summary,
        full_text=full_text,
        rapporteur=_text(source.get("magistrado"), source.get("relator"), source.get("relatora")),
        judgment_date=normalize_date(judgment_raw) if judgment_raw else None,
        publication_date=normalize_date(publication_raw) if publication_raw else None,
        source_updated_at=publication_raw,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE
        if (summary or full_text)
        else ExtractionStatus.PARTIAL,
        source_trace=trace,
        raw=raw,
        case_class=case_class,
        judging_body=judging_body,
        degree=degree,
        instance=instance,
        branch="state",
        authority="TJRN",
        collection="JURISPRUDENCIA",
        document_type=decision_type,
        source_origin=source_origin,
        document_url=_text(
            source.get("url_inteiro_teor"),
            source.get("link_inteiro_teor"),
            source.get("document_url"),
        ),
    )


def _total_from_hits(value: Any) -> int:
    if isinstance(value, dict):
        value = value.get("value")
    try:
        total = int(value)
    except (TypeError, ValueError) as exc:
        raise ParserContractChangedError("TJRN hits.total is not an integer") from exc
    if total < 0:
        raise ParserContractChangedError("TJRN hits.total cannot be negative")
    return total


def _text(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, list):
            value = value[0] if value else None
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _plain_text(value: str | None) -> str | None:
    """Normalize a provider text value without discarding its raw form."""

    if not value:
        return None
    if "<" not in value or ">" not in value:
        return _collapse_text(value)
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    return _collapse_text(text)


def _collapse_text(value: str) -> str | None:
    normalized = " ".join(value.split())
    normalized = re.sub(r"\s+([,.;:!?%])", r"\1", normalized)
    return normalized or None


def _normalize_degree(value: str | None) -> str | None:
    """Map TJRN numeric/textual degree labels to the canonical vocabulary."""

    if value is None:
        return None
    normalized = value.casefold().replace("º", "").replace("°", "").strip()
    compact = " ".join(normalized.split())
    if compact in {"1", "1o", "primeiro", "primeiro grau", "first", "first degree"}:
        return "first"
    if compact in {"2", "2o", "segundo", "segundo grau", "second", "second degree"}:
        return "second"
    if "recurs" in compact:
        return "recursal"
    if "superior" in compact:
        return "superior"
    if compact in {"misto", "mista", "mixed"}:
        return "mixed"
    return "unknown"


def _matches_local_filters(result: JurisprudenceResult, filters: dict[str, str]) -> bool:
    """Apply only fields explicitly exposed by a TJRN result.

    The endpoint does not document these refinements in its request schema,
    so they are deliberately local post-filters.  Missing values do not match
    a requested filter; this prevents an incomplete mixed page from being
    presented as a valid second-degree hit.
    """

    def contains(actual: str | None, expected: str) -> bool:
        return bool(actual and expected.casefold() in actual.casefold())

    if "degree" in filters and _normalize_degree(result.degree) != _normalize_degree(
        filters["degree"]
    ):
        return False
    if "instance" in filters and _normalize_degree(result.instance) != _normalize_degree(
        filters["instance"]
    ):
        return False
    if "case_class" in filters and not contains(result.case_class, filters["case_class"]):
        return False
    if "judging_body" in filters and not contains(result.judging_body, filters["judging_body"]):
        return False
    if "source_origin" in filters and not contains(result.source_origin, filters["source_origin"]):
        return False
    if "decision_type" in filters and not contains(result.type, filters["decision_type"]):
        return False
    judgment_date = normalize_date(result.judgment_date) if result.judgment_date else None
    if "judgment_date_from" in filters:
        start = normalize_date(filters["judgment_date_from"])
        if not judgment_date or not start or judgment_date < start:
            return False
    if "judgment_date_to" in filters:
        end = normalize_date(filters["judgment_date_to"])
        if not judgment_date or not end or judgment_date > end:
            return False
    return True


__all__ = [
    "TJRN_ENDPOINT",
    "TjrnJurisprudenciaProvider",
    "build_tjrn_payload",
    "parse_tjrn_response",
]
