"""TJDFT public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime
from typing import Any
from urllib.parse import urlencode, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from nanojuris.adaptive_selectors import SelectorMemory, resilient_select
from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import build_canonical_document
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
    UnsupportedQueryError,
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
from nanojuris.parsing import parse_html
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import (
    TransportPolicy,
    TransportRequest,
    TransportResponse,
    TransportStatus,
)

TJDF_JURIS_ENDPOINT = "/IndexadorAcordaos-web/sistj"
TJDF_JURIS_API_ENDPOINT = "/api/v1/pesquisa"


class TjdfJurisProvider(JurisprudenceProvider):
    """Provider for TJDFT SISTJ public jurisprudence search."""

    name = "tjdf_juris"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
        use_api: bool | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        hosts = tuple(
            host
            for host in (
                urlsplit(self.config.tjdf_juris_url).hostname,
                urlsplit(self.config.tjdf_juris_api_url).hostname,
            )
            if host
        )
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=hosts,
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
        self._last_response_content = b""
        self.use_api = self.config.tjdf_juris_api_enabled if use_api is None else use_api

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        if self.use_api:
            return self._search_api(query)
        initial_params = _build_initial_params(query)
        initial_html = self._request_text("GET", TJDF_JURIS_ENDPOINT, params=initial_params)
        total = parse_tjdf_total(initial_html)

        results_params = _build_results_params(query, total=total)
        results_html = self._request_text("GET", TJDF_JURIS_ENDPOINT, params=results_params)
        document_ids = parse_tjdf_result_ids(results_html)[: query.page_size]
        results_trace = _trace_with_http_metadata(
            SourceTrace(
                provider=self.name,
                endpoint=TJDF_JURIS_ENDPOINT,
                query=results_params,
                source_url=urljoin(self.config.tjdf_juris_url, TJDF_JURIS_ENDPOINT.lstrip("/")),
                limitations=[
                    "Fonte HTML publica do TJDFT/SISTJ sujeita a mudancas de layout.",
                    "Busca validada por sessao HTTP limpa, sem captcha ou login no fluxo testado.",
                    "Detalhes sao coletados sob demanda quando fetch_details=True.",
                ],
            ),
            self._last_http_metadata,
        )
        if query.fetch_details:
            results = [
                parse_tjdf_detail(
                    self._request_text(
                        "GET", TJDF_JURIS_ENDPOINT, params=_build_detail_params(item)
                    ),
                    document_id=item,
                    trace=_trace_with_http_metadata(results_trace, self._last_http_metadata),
                )
                for item in document_ids
            ]
        else:
            results = parse_tjdf_list_results(
                results_html, trace=results_trace, base_url=self.config.tjdf_juris_url
            )[: query.page_size]
        trace = results_trace
        start = ((query.page - 1) * query.page_size) + 1 if results else 0
        complete, completeness_reason = page_completeness(
            reported_total=total,
            start=start,
            returned=len(results),
            total_is_authoritative=_tjdf_total_is_authoritative(initial_html),
        )
        return SearchPage(
            source=self.name,
            total=total,
            start=start,
            end=start + len(results) - 1 if results else 0,
            page=query.page,
            page_size=query.page_size,
            results=results,
            source_trace=trace,
            pagination_mode="page",
            is_complete=complete,
            completeness_reason=completeness_reason,
            total_known=total is not None,
            access_status=AccessStatus.PUBLIC,
            extraction_status=(ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY),
        )

    def _search_api(self, query: JurisprudenceQuery) -> SearchPage:
        """Search the documented TJDFT JSON surface without creating a provider.

        The API uses zero-based ``pagina`` while NanoJuris exposes one-based
        pages. This method converts only the transport payload and keeps the
        public ``SearchPage.page`` contract unchanged.
        """

        payload = _build_api_payload(query)
        response_payload = self._request_json(TJDF_JURIS_API_ENDPOINT, payload)
        trace = _trace_with_http_metadata(
            SourceTrace(
                provider=self.name,
                endpoint=TJDF_JURIS_API_ENDPOINT,
                query=payload,
                source_url=urljoin(
                    self.config.tjdf_juris_api_url,
                    TJDF_JURIS_API_ENDPOINT.lstrip("/"),
                ),
                limitations=[
                    "API JSON publica do TJDFT; contrato de campos pode variar por classe.",
                    "A API nao publicou uma rota separada de detalhe nesta validacao.",
                    "O campo possuiInteiroTeor nao prova sozinho a disponibilidade do texto.",
                ],
                transformations=["pagina_api_zero_based_convertida"],
            ),
            self._last_http_metadata,
        )
        return parse_tjdf_api_response(
            response_payload,
            trace=trace,
            page=query.page,
            page_size=query.page_size,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document_id = _normalize_tjdf_document_id(precedent_id)
        html = self._request_text(
            "GET", TJDF_JURIS_ENDPOINT, params=_build_detail_params(document_id)
        )
        _extract_detail_fields_or_raise(html, document_id)
        trace = SourceTrace(
            provider=self.name,
            endpoint=TJDF_JURIS_ENDPOINT,
            query=_build_detail_params(document_id),
            source_url=urljoin(self.config.tjdf_juris_url, TJDF_JURIS_ENDPOINT.lstrip("/")),
            limitations=["Detalhe publico de acordao TJDFT/SISTJ."],
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": html, "content_type": "text/html"}],
            source_trace=trace,
            raw={"numeroDoDocumento": document_id},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        normalized_document_id = _normalize_tjdf_document_id(document_id)
        canonical_document_id = f"tjdf-acordao-{normalized_document_id}"
        html = self._request_text(
            "GET", TJDF_JURIS_ENDPOINT, params=_build_detail_params(normalized_document_id)
        )
        _extract_detail_fields_or_raise(html, normalized_document_id)
        trace = SourceTrace(
            provider=self.name,
            endpoint=TJDF_JURIS_ENDPOINT,
            query=_build_detail_params(normalized_document_id),
            source_url=urljoin(self.config.tjdf_juris_url, TJDF_JURIS_ENDPOINT.lstrip("/")),
            limitations=["Documento HTML publico do TJDFT/SISTJ."],
        )
        trace = _trace_with_http_metadata(trace, self._last_http_metadata)
        soup = BeautifulSoup(html, "html.parser")
        text = _normalize_spaces(soup.get_text(" ", strip=True))
        content = self._last_response_content or html.encode("utf-8")
        return build_canonical_document(
            document_id=canonical_document_id,
            source=self.name,
            document_type="acordao",
            content=content,
            content_type=self._last_http_metadata.get("content_type") or "text/html",
            title=f"TJDFT acordao {document_id}",
            text_override=text,
            url=trace.source_url,
            access_status=AccessStatus.PUBLIC,
            source_trace=trace,
            raw_metadata={"numeroDoDocumento": normalized_document_id},
            parser="tjdf_juris.get_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJDFT Jurisprudencia/SISTJ",
            source_url=self.config.tjdf_juris_url,
            category="court_jurisprudence",
            search_modes=["text", "summary", "date_range", "page", "document_id"],
            document_types=["acordao", "turma_recursal", "tema", "informativo"],
            # Keep the generated coverage catalog stable; the API JSON surface
            # is documented in ``endpoints`` and can be selected explicitly.
            content_formats=["html", "json"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "registry_number",
                "case_number",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "decision_outcome",
                "document_url",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "POST https://jurisdf.tjdft.jus.br/api/v1/pesquisa",
                "GET /IndexadorAcordaos-web/sistj?nomeDaPagina=buscaLivre",
                "GET /IndexadorAcordaos-web/sistj?nomeDaPagina=buscaLivre2",
                "GET /IndexadorAcordaos-web/sistj?comando=abrirDadosDoAcordao",
            ],
            supports_full_text=True,
            full_text_access="detail_call",
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            pagination_mode="page",
            completeness_contract="reported_total_and_page_window",
            supported_filters=[
                "text",
                "exact_phrase",
                "all_words",
                "any_words",
                "without_words",
                "number",
                "rapporteur",
                "source_origin",
                "source_origins",
                "case_class",
                "judging_body",
                "published_from",
                "published_to",
                "updated_from",
                "updated_to",
                "judgment_date_from",
                "judgment_date_to",
                "fetch_details",
            ],
            unsupported_filters=[
                "courts",
                "types",
                "decision_type",
                "lawyer_name",
                "legal_area",
                "oab",
                "party_document",
                "party_name",
                "police_document",
                "precatory_number",
                "cda",
                "source_origins",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "translated",
                "all_words": "translated",
                "any_words": "translated",
                "without_words": "translated",
                "number": "translated",
                "rapporteur": "translated",
                "source_origin": "translated",
                "source_origins": "translated",
                "case_class": "translated",
                "judging_body": "translated",
                "published_from": "translated",
                "published_to": "translated",
                "updated_from": "translated",
                "updated_to": "translated",
                "judgment_date_from": "translated",
                "judgment_date_to": "translated",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "courts": "unsupported",
                "types": "unsupported",
                "fetch_details": "native",
                "decision_type": "unsupported",
                "lawyer_name": "unsupported",
                "legal_area": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "cda": "unsupported",
            },
            limitations=[
                "A superficie JSON permanece selecionavel para compatibilidade com o HTML legado.",
                "Contrato HTML legado do SISTJ/TJDFT pode mudar sem aviso.",
                "Inteiro teor PJe pode depender de link/documento externo.",
                "Provider nao interpreta merito juridico nem substitui fonte oficial.",
            ],
            responsible_use=[
                "Usar com rate limit em coletas paginadas.",
                "Preservar SourceTrace e numeroDoDocumento para auditoria.",
            ],
        )

    def _request_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = urljoin(self.config.tjdf_juris_api_url.rstrip("/") + "/", path.lstrip("/"))
        request = TransportRequest(
            source=self.name,
            operation="jurisprudence_api",
            method="POST",
            url=url,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": self.config.user_agent,
            },
            json_body=payload,
            idempotent=False,
        )
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJDFT API request failed: {exc}") from exc
        self._raise_transport_error(response, "TJDFT API", unsupported_query=True)
        content = bytes(response.body)
        self._record_response(response, url, content)
        try:
            data = response.json()
        except (TypeError, ValueError) as exc:
            raise ParserContractChangedError("TJDFT API returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJDFT API returned a non-object JSON payload")
        return data

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        url = urljoin(self.config.tjdf_juris_url.rstrip("/") + "/", path.lstrip("/"))
        request = TransportRequest(
            source=self.name,
            operation="sistj_request",
            method=method,
            url=url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "User-Agent": self.config.user_agent,
                **kwargs.pop("headers", {}),
            },
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
            raise SourceUnavailableError(f"TJDFT/SISTJ request failed: {exc}") from exc
        self._raise_transport_error(response, "TJDFT/SISTJ")
        content = bytes(response.body)
        self._record_response(response, url, content)
        return _decode_response_text(content, response.content_type)

    @staticmethod
    def _raise_transport_error(
        response: TransportResponse,
        label: str,
        *,
        unsupported_query: bool = False,
    ) -> None:
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"{label} transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError(f"{label} transport returned no HTTP status")
        if status_code == 429:
            raise RateLimitDetectedError(f"{label} returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(
                f"{label} requires access validation (HTTP {status_code})"
            )
        if unsupported_query and status_code in {400, 422}:
            raise UnsupportedQueryError(f"{label} rejected query with HTTP {status_code}")
        if status_code >= 500:
            raise SourceUnavailableError(f"{label} returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(f"{label} rejected request with HTTP {status_code}")

    def _record_response(
        self, response: TransportResponse, request_url: str, content: bytes
    ) -> None:
        status_code = response.status_code
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": str(response.final_url or request_url),
            "content_type": response.content_type,
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": (
                "ok" if status_code is not None and 200 <= status_code < 300 else "http_error"
            ),
        }
        self._last_response_content = content


def _decode_response_text(content: bytes, content_type: str | None) -> str:
    """Decode bounded transport bytes using an advertised charset when present."""

    charset = None
    if content_type:
        match = re.search(r"charset\s*=\s*['\"]?([^;\s'\"]+)", content_type, re.I)
        if match:
            charset = match.group(1)
    # SISTJ has historically omitted or misreported its charset while
    # returning UTF-8 bytes. Prefer a strict UTF-8 decode first; genuine
    # ISO-8859-1 pages fall through to the advertised/legacy encodings when
    # their byte sequence is not valid UTF-8.
    for encoding in ("utf-8", charset, "ISO-8859-1"):
        if not encoding:
            continue
        try:
            return content.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return content.decode("utf-8", errors="replace")


def _trace_with_http_metadata(trace: SourceTrace, metadata: dict[str, Any]) -> SourceTrace:
    """Attach observed transport facts without inferring unavailable values."""

    return SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
        source_url=trace.source_url,
        limitations=trace.limitations,
        http_status=metadata.get("http_status"),
        final_url=metadata.get("final_url"),
        content_type=metadata.get("content_type"),
        content_sha256=metadata.get("content_sha256"),
        response_bytes=metadata.get("response_bytes"),
        elapsed_ms=metadata.get("elapsed_ms"),
        retrieval_status=metadata.get("retrieval_status"),
        transformations=trace.transformations,
    )


def _build_api_payload(query: JurisprudenceQuery) -> dict[str, Any]:
    """Build only fields documented by the TJDFT JSON API."""

    terms: list[dict[str, str]] = []
    mappings = (
        ("number", "processo"),
        ("rapporteur", "nomeRelator"),
        ("source_origin", "origem"),
        ("case_class", "descricaoClasseCnj"),
        ("judging_body", "descricaoOrgaoJulgador"),
        ("updated_from", "dataJulgamento"),
        ("updated_to", "dataJulgamento"),
        ("published_from", "dataPublicacao"),
        ("published_to", "dataPublicacao"),
        ("judgment_date_from", "dataJulgamento"),
        ("judgment_date_to", "dataJulgamento"),
    )
    for query_field, api_field in mappings:
        value = getattr(query, query_field, "")
        if value:
            terms.append({"campo": api_field, "valor": _api_date_or_text(value)})
    for value in query.source_origins:
        if value:
            terms.append({"campo": "origem", "valor": str(value)})
    payload: dict[str, Any] = {
        "query": _build_search_expression(query),
        # API pages are zero-based; the public NanoJuris query remains one-based.
        "pagina": query.page - 1,
        "tamanho": query.page_size,
        # These switches are published by the official JURISDF client. They
        # make the response carry the ementa/decisao and inteiro teor when the
        # source has it, while the parser still treats availability as
        # record-specific rather than trusting a boolean flag.
        "sinonimos": True,
        "espelho": True,
        "inteiroTeor": True,
        "retornaInteiroTeor": True,
        "retornaTotalizacao": True,
    }
    if terms:
        payload["termosAcessorios"] = terms
    return payload


def _api_date_or_text(value: str) -> str:
    """Normalize accepted public query dates without changing other filters."""

    text = str(value).strip()
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    return text


def parse_tjdf_api_response(
    payload: dict[str, Any],
    *,
    trace: SourceTrace,
    page: int,
    page_size: int,
) -> SearchPage:
    """Parse the documented JSON envelope and retain unknown fields in raw records."""

    if "hits" not in payload or "registros" not in payload:
        raise ParserContractChangedError(
            "TJDFT API response missing required hits or registros fields"
        )
    hits = payload["hits"]
    if isinstance(hits, dict):
        total = hits.get("value")
    else:
        total = hits
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ParserContractChangedError("TJDFT API response has invalid hits total")
    records_payload = payload["registros"]
    if not isinstance(records_payload, list):
        raise ParserContractChangedError("TJDFT API response has invalid registros list")
    if any(not isinstance(item, dict) for item in records_payload):
        raise ParserContractChangedError("TJDFT API response has a non-object registro")
    results = [_parse_tjdf_api_record(item, trace=trace) for item in records_payload]
    aggregations = payload.get("agregacoes", {})
    if aggregations is None:
        aggregations = {}
    if not isinstance(aggregations, dict):
        raise ParserContractChangedError("TJDFT API response has invalid agregacoes object")
    start = ((page - 1) * page_size) + 1 if results else 0
    complete, completeness_reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        total_is_authoritative=True,
    )
    return SearchPage(
        source="tjdf_juris",
        total=total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=page,
        page_size=page_size,
        results=results,
        aggregations=aggregations,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=completeness_reason,
        total_known=True,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY),
    )


def _parse_tjdf_api_record(
    record: dict[str, Any],
    *,
    trace: SourceTrace,
) -> JurisprudenceResult:
    external_id = record.get("uuid") or record.get("identificador")
    if not external_id:
        raise ParserContractChangedError("TJDFT API record missing uuid and identificador")
    identifier = str(external_id)
    summary = _as_text(record.get("ementa"))
    full_text = _tjdf_api_full_text(record)
    base = _as_text(record.get("base"))
    subbase = _as_text(record.get("subbase"))
    record_type = " / ".join(value for value in (base, subbase) if value) or "acordao"
    publication_date = _normalize_tjdf_api_date(record.get("dataPublicacao"))
    judgment_date = _normalize_tjdf_api_date(record.get("dataJulgamento"))
    case_class = _as_text(record.get("descricaoClasseCnj") or record.get("classe"))
    judging_body = _as_text(record.get("descricaoOrgaoJulgador") or record.get("descricaoOrgao"))
    return JurisprudenceResult(
        id=f"tjdf-api-{identifier}",
        source="tjdf_juris",
        court="TJDFT",
        type=record_type,
        number=record.get("processo") or identifier,
        summary=summary,
        full_text=full_text,
        status=_as_text(record.get("decisao")),
        rapporteur=_as_text(record.get("nomeRelator")),
        updated_at=publication_date,
        judgment_date=judgment_date,
        publication_date=publication_date,
        source_updated_at=publication_date,
        case_class=case_class,
        judging_body=judging_body,
        degree="second",
        instance="second",
        branch="state",
        authority="TJDFT",
        collection="CJSG",
        document_type="acordao",
        source_origin=base or subbase,
        document_url=_as_text(record.get("url") or record.get("documentUrl")),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw=dict(record),
        field_provenance={
            "degree": {"source": "source_contract:tjdft_sistj_acordaos"},
            "instance": {"source": "source_contract:tjdft_sistj_acordaos"},
            "branch": {"source": "source_contract:tjdft"},
            "authority": {"source": "source_contract:tjdft"},
            "collection": {"source": "source_contract:tjdft_sistj_acordaos"},
        },
    )


def _tjdf_api_full_text(record: dict[str, Any]) -> str | None:
    for field in ("inteiroTeor", "inteiroTeorHtml"):
        value = _as_text(record.get(field))
        if value and not _tjdf_unavailable_text(value):
            return value
    return None


def _tjdf_unavailable_text(value: str) -> bool:
    normalized = _normalize_key(value)
    return "indisponivel" in normalized or "nao_disponivel" in normalized


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_tjdf_api_date(value: Any) -> str | None:
    text = _as_text(value)
    if not text:
        return None
    candidate = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate).date().isoformat()
    except ValueError:
        pass
    for pattern in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:10], pattern).date().isoformat()
        except ValueError:
            continue
    return None


def parse_tjdf_total(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    values = [
        _normalize_spaces(node.get_text(" ", strip=True))
        for node in soup.select(".conteudoComRotulo")
    ]
    for value in reversed(values):
        if value.isdigit():
            return int(value)
    match = re.search(r"Resultado.*?(\d+)", _normalize_spaces(soup.get_text(" ", strip=True)))
    return int(match.group(1)) if match else 0


def _tjdf_total_is_authoritative(html: str) -> bool:
    """Return whether the initial SISTJ page exposed a result count."""

    soup = BeautifulSoup(html, "html.parser")
    if any(
        _normalize_spaces(node.get_text(" ", strip=True)).isdigit()
        for node in soup.select(".conteudoComRotulo")
    ):
        return True
    return bool(re.search(r"Resultado.*?\d+", _normalize_spaces(soup.get_text(" ", strip=True))))


def parse_tjdf_result_ids(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    ids: list[str] = []
    for node in soup.select("#id_link_abrir_dados_acordao, [id*=id_link_abrir_dados_acordao]"):
        value = _normalize_spaces(node.get_text(" ", strip=True)) or str(node.get("value") or "")
        if value and value.isdigit() and value not in ids:
            ids.append(value)
    return ids


# The list row concatenates row index, registry id, an occurrence count (or the
# literal "Segredo de Justica/Justiça"), the rapporteur and the CNJ number
# before the ementa. Keep only the ementa for the canonical summary.
_TJDF_LIST_ROW = re.compile(
    r"Relator\(a\)\s*:\s*(?P<rapporteur>.+?)\s+"
    r"Processo\s*:\s*(?P<number>[\d.\-]+)\s+"
    r"(?P<ementa>.+)",
    re.IGNORECASE | re.DOTALL,
)

# SISTJ appends the judgment date, publication date and the judging body to
# the end of each list row.  The body label is not stable (for example,
# ``7ª Turma Cível`` or ``2a Turma Civel``), so only the two dates are part of
# the contract and the remaining suffix is treated as presentation metadata.
_TJDF_LIST_DATE_SUFFIX = re.compile(
    r"(?P<judgment_date>\d{2}/\d{2}/\d{4})\s+"
    r"(?P<publication_date>\d{2}/\d{2}/\d{4})"
    r"(?:\s+.*)?\s*$",
    re.IGNORECASE | re.DOTALL,
)


def _extract_tjdf_list_dates(value: str) -> tuple[str | None, str | None, str]:
    """Extract trailing SISTJ dates and return text without presentation suffix.

    Dates are emitted only by the live HTML list contract; older fixtures and
    alternate layouts may omit them.  In that case the original text is
    returned unchanged so the parser remains lossless.
    """

    match = _TJDF_LIST_DATE_SUFFIX.search(value)
    if not match:
        return None, None, value
    prefix = value[: match.start()].rstrip(" -;,.\t\r\n")
    return match.group("judgment_date"), match.group("publication_date"), prefix


def _split_tjdf_list_row(
    list_text: str, *, document_id: str
) -> tuple[str | None, str | None, str | None]:
    """Return (summary, rapporteur, process_number) from a list container blob."""

    if not list_text or list_text == document_id:
        return None, None, None
    match = _TJDF_LIST_ROW.search(list_text)
    if match:
        return (
            _normalize_spaces(match.group("ementa")).strip() or None,
            _normalize_spaces(match.group("rapporteur")).strip() or None,
            _normalize_spaces(match.group("number")).strip() or None,
        )
    # No recognizable header: drop a leading "<index> <registry-id> " prefix so
    # the summary does not start with bare identifiers, then fall back to the row.
    trimmed = re.sub(rf"^\s*\d+\s+{re.escape(document_id)}\s+", "", list_text).strip()
    return trimmed or None, None, None


def _tjdf_document_url(base_url: str, document_id: str) -> str | None:
    """Public SISTJ acórdão view for a registry id."""

    if not base_url:
        return None
    endpoint = urljoin(base_url.rstrip("/") + "/", TJDF_JURIS_ENDPOINT.lstrip("/"))
    return f"{endpoint}?{urlencode(_build_detail_params(document_id))}"


def parse_tjdf_list_results(
    html: str,
    *,
    trace: SourceTrace,
    base_url: str = "",
    memory: SelectorMemory | None = None,
) -> list[JurisprudenceResult]:
    """Parse list-page metadata without issuing one detail request per result.

    The acordao link selector is resolved through ``resilient_select`` so a
    layout change on the SISTJ result page relocates the rows by structure
    instead of silently returning nothing; any relocation is recorded on the
    ``SourceTrace``.
    """

    document = parse_html(html)
    row_links = resilient_select(
        document,
        "#id_link_abrir_dados_acordao, [id*=id_link_abrir_dados_acordao]",
        name="acordao_link",
        source="tjdf_juris",
        memory=memory,
        trace=trace,
    )
    results: list[JurisprudenceResult] = []
    for node in row_links:
        document_id = _normalize_spaces(node.text()) or str(node.get("value") or "")
        if not document_id.isdigit():
            continue
        container = node.find_parent(["article", "li", "tr", "div"]) or node
        list_text = _normalize_spaces(container.text())
        summary, rapporteur, process_number = _split_tjdf_list_row(
            list_text, document_id=document_id
        )
        judgment_date, publication_date, summary_without_dates = _extract_tjdf_list_dates(
            summary or ""
        )
        summary = summary_without_dates or None
        results.append(
            JurisprudenceResult(
                id=f"tjdf-acordao-{document_id}",
                source="tjdf_juris",
                court="TJDFT",
                type="acordao",
                number=document_id,
                summary=summary,
                rapporteur=rapporteur,
                updated_at=publication_date or judgment_date,
                judgment_date=judgment_date,
                publication_date=publication_date,
                source_updated_at=publication_date or judgment_date,
                degree="second",
                instance="second",
                branch="state",
                authority="TJDFT",
                collection="CJSG",
                document_type="acordao",
                document_url=_tjdf_document_url(base_url, document_id),
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.PARTIAL,
                source_trace=trace,
                raw={
                    "registry_number": document_id,
                    "process_number": process_number,
                    "judgment_date": judgment_date,
                    "publication_date": publication_date,
                    "document_url": _tjdf_document_url(base_url, document_id),
                    "list_metadata_only": True,
                    "list_text": list_text,
                },
            )
        )
    return results


def parse_tjdf_detail(html: str, *, document_id: str, trace: SourceTrace) -> JurisprudenceResult:
    fields = _extract_detail_fields_or_raise(html, document_id)
    case_text = fields.get("classe_do_processo", "")
    registry_number = fields.get("registro_do_acordao_numero") or document_id
    judgment_date = fields.get("data_de_julgamento")
    publication_text = fields.get("data_da_intimacao_ou_da_publicacao", "")
    publication_date = _extract_date(publication_text)
    summary = fields.get("ementa")
    decision_outcome = fields.get("decisao")
    document_url = trace.source_url
    case_number = _extract_case_number(case_text)
    result_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query={"numeroDoDocumento": document_id},
        source_url=document_url,
        limitations=trace.limitations,
        http_status=trace.http_status,
        final_url=trace.final_url,
        content_type=trace.content_type,
        content_sha256=trace.content_sha256,
        response_bytes=trace.response_bytes,
        elapsed_ms=trace.elapsed_ms,
        retrieval_status=trace.retrieval_status,
        transformations=trace.transformations,
    )
    return JurisprudenceResult(
        id=f"tjdf-acordao-{registry_number}",
        source="tjdf_juris",
        court="TJDFT",
        type="acordao",
        number=case_number or registry_number,
        summary=summary,
        status=decision_outcome,
        rapporteur=fields.get("relatora"),
        degree="second",
        instance="second",
        branch="state",
        authority="TJDFT",
        collection="CJSG",
        document_type="acordao",
        document_url=document_url,
        updated_at=publication_date or judgment_date,
        access_status=AccessStatus.PUBLIC if result_trace.http_status == 200 else None,
        source_trace=result_trace,
        raw={
            "registry_number": registry_number,
            "case_number": case_number,
            "case_class": _extract_case_class(case_text),
            "judging_body": fields.get("orgao_julgador"),
            "judgment_date": judgment_date,
            "publication_date": publication_date,
            "publication_text": publication_text,
            "decision_outcome": decision_outcome,
            "document_url": document_url,
            "fields": fields,
        },
    )


def _build_initial_params(query: JurisprudenceQuery) -> dict[str, str]:
    search_text = _build_search_expression(query)
    return {
        "argumentoDePesquisa": search_text,
        "visaoId": "tjdf.sistj.acordaoeletronico.buscaindexada.apresentacao.VisaoBuscaAcordao",
        "nomeDaPagina": "buscaLivre",
        "comando": "pesquisar",
        "internet": "1",
        "camposSelecionados": "ESPELHO",
        "COMMAND": "ok",
        "quantidadeDeRegistros": str(query.page_size),
        "tokenDePaginacao": str(query.page),
    }


def _build_results_params(query: JurisprudenceQuery, *, total: int) -> dict[str, str]:
    search_text = _build_search_expression(query)
    date_type, date_start, date_end = _build_date_params(query)
    return {
        "visaoId": "tjdf.sistj.acordaoeletronico.buscaindexada.apresentacao.VisaoBuscaAcordao",
        "nomeDaPagina": "buscaLivre2",
        "buscaPorQuery": "1",
        "baseSelecionada": "BASE_ACORDAO_TODAS",
        "ramoJuridico": "",
        "baseDados": "[BASE_ACORDAOS, TURMAS_RECURSAIS, BASE_ACORDAO_PJE, BASE_HISTORICA]",
        "argumentoDePesquisa": search_text,
        "desembargador": query.rapporteur,
        "indexacao": "",
        "tipoDeNumero": "",
        "tipoDeRelator": "",
        "camposSelecionados": "[ESPELHO]",
        "numero": "",
        "tipoDeData": date_type,
        "dataFim": date_end,
        "dataInicio": date_start,
        "ementa": query.exact_phrase,
        "orgaoJulgador": "",
        "legislacao": "",
        "numeroDaPaginaAtual": str(query.page),
        "quantidadeDeRegistros": str(query.page_size),
        "totalHits": str(total),
    }


def _build_search_expression(query: JurisprudenceQuery) -> str:
    """Translate boolean query fields to the SISTJ public query syntax."""

    expression = query.text.strip()
    if query.exact_phrase and not expression:
        expression = query.exact_phrase.strip()
    elif query.exact_phrase and query.exact_phrase.strip() not in expression:
        expression = f'{expression} "{query.exact_phrase.strip()}"'.strip()
    if query.all_words:
        expression = f'{expression} e "{query.all_words.strip()}"'.strip()
    if query.any_words:
        expression = f'{expression} ou ("{query.any_words.strip()}")'.strip()
    if query.without_words:
        expression = f'{expression} nao ("{query.without_words.strip()}")'.strip()
    return expression


def _build_date_params(query: JurisprudenceQuery) -> tuple[str, str, str]:
    """Map the two canonical date meanings to SISTJ's selector values."""

    if query.published_from or query.published_to:
        return "DataPublicacao", query.published_from, query.published_to
    if query.updated_from or query.updated_to:
        return "DataJulgamento", query.updated_from, query.updated_to
    return "", "", ""


def _build_detail_params(document_id: str) -> dict[str, str]:
    view_id = "tjdf.sistj.acordaoeletronico.buscaindexada.apresentacao.VisaoBuscaAcordao"
    controller_id = (
        "tjdf.sistj.acordaoeletronico.buscaindexada.apresentacao.ControladorBuscaAcordao"
    )
    return {
        "visaoId": view_id,
        "controladorId": controller_id,
        "visaoAnterior": view_id,
        "nomeDaPagina": "resultado",
        "comando": "abrirDadosDoAcordao",
        "enderecoDoServlet": "sistj",
        "historicoDePaginas": "buscaLivre",
        "quantidadeDeRegistros": "20",
        "baseSelecionada": "BASE_ACORDAO_TODAS",
        "numeroDaUltimaPagina": "1",
        "buscaIndexada": "1",
        "mostrarPaginaSelecaoTipoResultado": "false",
        "totalHits": "1",
        "internet": "1",
        "numeroDoDocumento": document_id,
    }


def _normalize_tjdf_document_id(document_id: str) -> str:
    return re.sub(r"^tjdf-acordao-", "", document_id.strip(), flags=re.I)


def _extract_labeled_fields(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    fields: dict[str, str] = {}
    for label_node in soup.select(".rotulo"):
        label = _normalize_key(label_node.get_text(" ", strip=True))
        parent = label_node.find_parent("div")
        value_node = parent.select_one(".conteudoComRotulo") if parent else None
        value = _normalize_spaces(value_node.get_text(" ", strip=True)) if value_node else ""
        if label and value:
            fields[label] = value
    return fields


def _extract_detail_fields_or_raise(html: str, document_id: str) -> dict[str, str]:
    fields = _extract_labeled_fields(html)
    if not any(
        fields.get(key) for key in ("ementa", "classe_do_processo", "registro_do_acordao_numero")
    ):
        raise ParserContractChangedError(
            f"TJDFT/SISTJ detail for document {document_id!r} returned no acórdão fields"
        )
    return fields


def _extract_case_number(value: str) -> str | None:
    masked = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", value)
    if masked:
        return masked.group(0)
    unmasked = re.search(r"\b\d{20}\b", value)
    return unmasked.group(0) if unmasked else None


def _extract_case_class(value: str) -> str | None:
    parts = [part.strip(" -()") for part in value.split(" - ") if part.strip(" -()")]
    if len(parts) >= 2:
        return parts[-1]
    return None


def _extract_date(value: str) -> str | None:
    match = re.search(r"\b\d{2}/\d{2}/\d{4}\b", value)
    return match.group(0) if match else None


def _normalize_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("(a)", "a")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
