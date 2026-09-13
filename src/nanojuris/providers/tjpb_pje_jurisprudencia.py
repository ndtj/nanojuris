"""TJPB/PJe public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

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
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import (
    TransportPolicy,
    TransportRequest,
    TransportResponse,
    TransportStatus,
)

TOKEN_RE = re.compile(r'<meta[^>]+name=["\']_token["\'][^>]+content=["\']([^"\']+)', re.IGNORECASE)


class TjpbPjeJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the public TJPB PJe jurisprudence database."""

    name = "tjpb_pje_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlsplit(self.config.tjpb_pje_jurisprudencia_url).hostname or ""
        self.transport = SharedHttpClient(
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
        self._last_http_metadata: dict[str, Any] = {}

    @property
    def base_url(self) -> str:
        return self.config.tjpb_pje_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_degree_scope(query)
        token = self._get_token()
        page = max(query.page, 1)
        payload = {
            "_token": token,
            "jurisprudencia": _build_search_object(query),
            "page": page,
        }
        endpoint = "/api/jurisprudencia/pesquisar"
        data, source_url = self._request_json("POST", endpoint, json=payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={
                **_public_query(query),
                "page": page,
                "page_size": _page_size(query.page_size),
                "body_contract": "tjpb_pje_jurisprudencia_v1",
            },
            source_url=source_url,
            limitations=[
                "O token CSRF e obtido da pagina publica a cada busca.",
                "A pagina do PJe e baseada em um; o provider preserva essa semantica.",
                "O provider nao resolve Cloudflare, captcha ou qualquer desafio humano.",
            ],
            **self._last_http_metadata,
        )
        return parse_tjpb_search_response(data, query=query, trace=trace, base_url=self.base_url)

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
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        external_id = _normalize_id(document_id)
        endpoint = f"/jurisprudencia/view/{external_id}"
        response = self._request("GET", endpoint, params={"words": ""})
        html = response.text
        source_url = str(response.final_url or self.base_url + endpoint)
        soup = BeautifulSoup(html, "html.parser")
        for element in soup.select("script, style, noscript, nav, footer"):
            element.decompose()
        content = soup.select_one("main") or soup.select_one("#jurisprudencia") or soup.body
        text = _normalize_text(content.get_text("\n", strip=True) if content else "")
        if not text:
            raise ParserContractChangedError("TJPB detail returned empty public content")
        content_bytes = bytes(response.body)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={"id": external_id},
            source_url=source_url,
            final_url=source_url,
            http_status=response.status_code,
            content_type=response.content_type,
            content_sha256=hashlib.sha256(content_bytes).hexdigest(),
            response_bytes=len(content_bytes),
        )
        return build_canonical_document(
            document_id=f"tjpb-pje-document-{external_id}",
            source=self.name,
            document_type="jurisprudencia",
            content=content_bytes,
            content_type=response.content_type or "text/html",
            title="TJPB PJe Jurisprudencia",
            url=source_url,
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"external_id": external_id},
            parser="tjpb_pje_jurisprudencia.get_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJPB PJe Jurisprudencia",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range", "catalog"],
            document_types=["jurisprudencia_pje", "acordao", "decisao"],
            content_formats=["json", "html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "summary",
                "judgment_date",
                "document_url",
                "search_score",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /",
                "GET /api/pje/origens/list",
                "GET /api/pje/classes/list/{id_origem}",
                "GET /api/pje/orgaosJulgadores/list/{id_origem}",
                "GET /api/pje/relatores/list/{id_orgao_julgador}",
                "POST /api/jurisprudencia/pesquisar",
                "GET /jurisprudencia/view/{id}?words={termos}",
            ],
            supports_full_text=True,
            full_text_access="detail_call",
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_live_tests=True,
            pagination_mode="page",
            completeness_contract="reported_total_and_page_window",
            supported_filters=[
                "text",
                "number",
                "case_class",
                "judging_body",
                "rapporteur",
                "published_from",
                "published_to",
                "judgment_date_from",
                "judgment_date_to",
                "source_origin",
                "degree",
                "instance",
            ],
            filter_semantics={
                "text": "translated",
                "all_words": "translated",
                "number": "translated",
                "case_class": "translated",
                "judging_body": "translated",
                "rapporteur": "translated",
                "lawyer_name": "translated",
                "source_origin": "translated",
                "source_origins": "translated",
                "published_from": "translated",
                "published_to": "translated",
                "judgment_date_from": "translated",
                "judgment_date_to": "translated",
                "degree": "native",
                "instance": "native",
                "types": "translated",
                "exact_phrase": "translated",
                "fetch_details": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "party_name": "unsupported",
                "party_document": "unsupported",
                "oab": "unsupported",
                "precatory_number": "unsupported",
                "police_document": "unsupported",
                "cda": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
                # The endpoint is a dedicated TJPB/CJSG surface.  These
                # dimensions are therefore validated scope rather than
                # user-selectable remote filters.
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                "courts": "unsupported",
                "legal_area": "unsupported",
                "decision_type": "translated",
                "document_type": "translated",
            },
            limitations=[
                "O token CSRF e dinamico e nao deve ser persistido.",
                "A pagina retornada pelo backend e limitada a dez itens por pagina.",
                "O detalhe e HTML publico; links de PDF nao foram promovidos.",
            ],
            responsible_use=[
                "Usar consultas especificas e rate limit configurado.",
                "Preservar o id externo e SourceTrace.",
                "Nao contornar desafios de acesso ou controles do tribunal.",
            ],
        )

    def _get_token(self) -> str:
        html, _ = self._request_text("GET", "/")
        match = TOKEN_RE.search(html)
        if not match:
            if _looks_like_access_control(html):
                raise AccessControlRequiredError(
                    "TJPB public page returned an access-control challenge"
                )
            raise ParserContractChangedError("TJPB page did not expose the public CSRF token")
        return match.group(1)

    def _request_json(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> tuple[dict[str, Any], str]:
        response = self._request(method, endpoint, **kwargs)
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJPB jurisprudence response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJPB jurisprudence JSON root is not an object")
        return data, str(response.final_url or self.base_url + endpoint)

    def _request_text(self, method: str, endpoint: str, **kwargs: Any) -> tuple[str, str]:
        response = self._request(method, endpoint, **kwargs)
        text = response.text
        if not text.strip():
            raise ParserContractChangedError("TJPB jurisprudence response is empty")
        return text, str(response.final_url or self.base_url + endpoint)

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> TransportResponse:
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        headers = {
            "Accept": "application/json, text/html, */*",
            "Content-Type": "application/json" if method == "POST" else "text/html",
            "User-Agent": self.config.user_agent,
            **({"X-Requested-With": "XMLHttpRequest"} if method == "POST" else {}),
            **kwargs.pop("headers", {}),
        }
        request = TransportRequest(
            source=self.name,
            operation="pje_jurisprudence_request",
            method=method,
            url=url,
            headers=headers,
            params=kwargs.pop("params", {}),
            data=kwargs.pop("data", None),
            json_body=kwargs.pop("json", None),
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPB jurisprudence request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJPB transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJPB transport returned no HTTP status")
        content = bytes(response.body)
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": str(response.final_url or url),
            "content_type": response.content_type,
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if status_code < 400 else "error",
        }
        if status_code == 429:
            raise RateLimitDetectedError("TJPB jurisprudence returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError("TJPB jurisprudence requires access validation")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJPB jurisprudence returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(
                f"TJPB jurisprudence rejected request with HTTP {status_code}"
            )
        return response


def parse_tjpb_search_response(
    data: dict[str, Any],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    """Parse the public TJPB JSON search envelope."""

    hits = data.get("hits")
    if not isinstance(hits, list):
        raise ParserContractChangedError("TJPB response missing hits list")
    page_size = _page_size(query.page_size)
    results = [
        _hit_to_result(item, trace=trace, base_url=base_url)
        for item in hits[:page_size]
        if isinstance(item, dict)
    ]
    total = _as_int(data.get("total"), default=len(results))
    page = max(query.page, 1)
    start = ((page - 1) * page_size) + 1 if results else 0
    complete, completeness_reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        total_is_authoritative="total" in data,
    )
    return SearchPage(
        source="tjpb_pje_jurisprudencia",
        total=total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=page,
        page_size=page_size,
        results=results,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=completeness_reason,
        total_known="total" in data,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY),
        filters_applied=_tjpb_filters_applied(query),
    )


def _hit_to_result(
    item: dict[str, Any], *, trace: SourceTrace, base_url: str
) -> JurisprudenceResult:
    external_id = _optional_str(item.get("_id"))
    if not external_id:
        raise ParserContractChangedError("TJPB result missing _id")
    summary = _clean_tjpb_ementa(_optional_str(item.get("ementa")))
    judgment_date = _optional_str(item.get("dt_ementa"))
    case_class = _optional_str(item.get("classe") or item.get("case_class"))
    # ``classe`` is a process-classification field, not a degree marker.  A
    # class or ementa may legitimately mention a sentence upheld on appeal;
    # only explicit degree/instance fields can reject the CJSG contract.
    _validate_record_degree(item=item)
    document_type = _document_type(case_class=case_class, summary=summary)
    document_url = urljoin(base_url + "/", f"jurisprudencia/view/{external_id}")
    return JurisprudenceResult(
        id=f"tjpb-pje-{external_id}",
        source="tjpb_pje_jurisprudencia",
        court="TJPB",
        type="jurisprudencia_pje",
        number=_optional_str(item.get("numero_processo")),
        summary=summary,
        judgment_date=judgment_date,
        updated_at=judgment_date,
        case_class=case_class,
        judging_body=_optional_str(item.get("orgao_julgador") or item.get("judging_body")),
        rapporteur=_optional_str(item.get("relator") or item.get("rapporteur")),
        degree="second",
        instance="second",
        branch="state",
        authority="TJPB",
        collection="CJSG",
        document_type=document_type,
        source_origin=_optional_str(item.get("origem") or item.get("source_origin")),
        document_url=document_url,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw={
            **item,
            "external_id": external_id,
            "document_url": document_url,
            "full_text_url": document_url,
            "degree": "second",
            "instance": "second",
            "branch": "state",
            "authority": "TJPB",
            "collection": "CJSG",
            "document_type": document_type,
        },
        field_provenance={
            "degree": {"source": "source_contract:pje_jurisprudencia_second_degree"},
            "instance": {"source": "source_contract:pje_jurisprudencia_second_degree"},
            "branch": {"source": "source_contract:tjpb"},
            "authority": {"source": "source_contract:tjpb"},
            "collection": {"source": "source_contract:pje_jurisprudencia_second_degree"},
        },
    )


def _tjpb_filters_applied(query: JurisprudenceQuery) -> dict[str, str]:
    """Describe filters represented in the public TJPB search object."""

    applied: dict[str, str] = {}
    if query.text:
        applied["text"] = "translated"
    if query.exact_phrase:
        applied["exact_phrase"] = "translated"
    if query.all_words:
        applied["all_words"] = "translated"
    if query.number:
        applied["number"] = "translated"
    if query.case_class:
        applied["case_class"] = "translated"
    if query.judging_body:
        applied["judging_body"] = "translated"
    if query.rapporteur:
        applied["rapporteur"] = "translated"
    if query.lawyer_name:
        applied["lawyer_name"] = "translated"
    if query.source_origin or query.source_origins:
        applied["source_origin"] = "translated"
    if query.types:
        applied["types"] = "translated"
    for name, value in (
        ("published_from", query.published_from),
        ("published_to", query.published_to),
        ("judgment_date_from", query.judgment_date_from),
        ("judgment_date_to", query.judgment_date_to),
    ):
        if value:
            applied[name] = "translated"
    if query.degree:
        applied["degree"] = "validated_scope"
    if query.instance:
        applied["instance"] = "validated_scope"
    return applied


def _validate_degree_scope(query: JurisprudenceQuery) -> None:
    """Reject first-degree/document scopes unsupported by the TJPB CJSG API."""

    values = {
        value.strip().casefold()
        for value in (*query.types, query.degree, query.instance)
        if value and value.strip()
    }
    first_degree = {"sentenca", "sentença", "first", "primeiro", "primeiro_grau", "1", "1o"}
    second_degree = {"second", "segundo", "segundo_grau", "2", "2o"}
    if values & first_degree:
        raise QueryRejectedError("TJPB PJe jurisprudencia exposes only second-degree decisions")
    # ``types`` contains document/process classes in normal queries; only
    # reject an unknown value when it came from the canonical degree fields.
    degree_values = {
        value.strip().casefold()
        for value in (query.degree, query.instance)
        if value and value.strip()
    }
    if degree_values and degree_values - second_degree:
        raise QueryRejectedError("TJPB PJe jurisprudencia supports only degree=second")


def _validate_record_degree(*, item: dict[str, Any]) -> None:
    """Guard the dedicated CJSG contract against an accidental first-degree hit."""

    values: list[str] = []
    for key in ("degree", "grau", "instance", "instancia", "tipo_instancia", "nivel"):
        value = item.get(key)
        if value is not None:
            values.append(str(value))
    for value in values:
        normalized_value = " ".join(str(value).casefold().replace("\u00ba", "o").split())
        if normalized_value in {
            "1",
            "1o",
            "1o grau",
            "first",
            "first degree",
            "primeiro",
            "primeiro grau",
            "sentenca",
        }:
            raise ParserContractChangedError("TJPB CJSG returned an explicit first-degree record")


def _document_type(*, case_class: str | None, summary: str | None) -> str:
    haystack = " ".join(value for value in (case_class, summary) if value).casefold()
    if "decis" in haystack and "monocrat" in haystack:
        return "decisao_monocratica"
    return "acordao"


def _build_search_object(query: JurisprudenceQuery) -> dict[str, Any]:
    types = {value.strip().lower() for value in query.types}
    origins = query.source_origin or ",".join(query.source_origins) or "8,2"
    case_class = query.case_class or (query.types[0] if query.types else "")
    judgment_from = query.judgment_date_from or query.published_from
    judgment_to = query.judgment_date_to or query.published_to
    return {
        "ementa": query.text or query.exact_phrase or "",
        "teor": query.all_words or "",
        # The public backend still expects this historical misspelling.
        "nr_rocesso": query.number,
        "id_classe_judicial": case_class,
        "id_orgao_julgador": query.judging_body or "",
        "id_relator": query.rapporteur or query.lawyer_name,
        "dt_inicio": judgment_from,
        "dt_fim": judgment_to,
        "id_origem": origins,
        "decisoes": bool(types & {"decisao", "decisão", "monocratica", "monocrática"}),
    }


def _public_query(query: JurisprudenceQuery) -> dict[str, Any]:
    return {
        "text": query.text,
        "all_words": query.all_words,
        "exact_phrase": query.exact_phrase,
        "number": query.number,
        "case_class": query.case_class,
        "judging_body": query.judging_body,
        "rapporteur": query.rapporteur,
        "lawyer_name": query.lawyer_name,
        "source_origin": query.source_origin,
        "source_origins": query.source_origins,
        "published_from": query.published_from,
        "published_to": query.published_to,
        "judgment_date_from": query.judgment_date_from,
        "judgment_date_to": query.judgment_date_to,
        "types": query.types,
        "degree": query.degree,
        "instance": query.instance,
    }


def _normalize_id(value: str) -> str:
    normalized = value.strip()
    if normalized.startswith("tjpb-pje-"):
        normalized = normalized.removeprefix("tjpb-pje-")
    if not normalized or len(normalized) > 160 or any(char.isspace() for char in normalized):
        raise ValueError("TJPB document id must be a non-empty external id")
    return normalized


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _looks_like_access_control(value: str) -> bool:
    """Identify a challenge page without treating it as an empty result."""

    normalized = value.casefold()
    return any(
        marker in normalized
        for marker in (
            "captcha",
            "recaptcha",
            "cloudflare",
            "cf-chl-",
            "access denied",
            "acesso negado",
            "verifique que voce e um humano",
        )
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


_TJPB_HEADER = re.compile(
    r"^\s*(?:Processo\s*n?[ºo]?\s*:.*?)?(?:EMENTA|E\s*M\s*E\s*N\s*T\s*A)\s*[-:.]?\s*",
    re.IGNORECASE | re.DOTALL,
)


def _clean_tjpb_ementa(summary: str | None) -> str | None:
    """Drop a leading process/parties metadata block from the ementa field.

    Some TJPB PJe records prefix the ementa with ``Processo nº: ... Classe: ...
    Assuntos: ... RECORRENTE: ...``, which produces near-identical synthesised
    titles. Keep only the text after the ``EMENTA`` marker.
    """

    if not summary:
        return summary
    match = _TJPB_HEADER.match(summary)
    if match:
        return summary[match.end() :].lstrip(" :.-").rstrip() or None
    if re.match(r"^\s*Processo\s*n?[ºo]?\s*:", summary, re.IGNORECASE):
        return None
    # "Poder Judiciário Gab. Des. <relator>   EMENTA..." — the gabinete line is
    # separated from the ementa by a run of whitespace; keep only the ementa.
    gab = re.match(
        r"^\s*Poder\s+Judici[áa]rio\b.*?\s{2,}(\S.*)$",
        summary,
        re.IGNORECASE | re.DOTALL,
    )
    if gab:
        return gab.group(1).lstrip(" :.-").rstrip() or None
    if re.match(r"^\s*Poder\s+Judici[áa]rio\b", summary, re.IGNORECASE):
        return None
    return summary


def _as_int(value: object, *, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 10))
