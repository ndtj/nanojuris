"""TJRS public AJAX/SOLR jurisprudence provider."""

from __future__ import annotations

import base64
import hashlib
from typing import Any
from urllib.parse import quote_plus, urljoin, urlparse

import requests

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
from nanojuris.normalization import normalize_date_value
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import (
    TransportPolicy,
    TransportRequest,
    TransportStatus,
)


class TjrsSolrProvider(JurisprudenceProvider):
    """Provider for the public TJRS jurisprudence AJAX endpoint."""

    name = "tjrs_solr"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
        *,
        ocr_allowed: bool = False,
        ocr_max_pages: int = 5,
        ocr_timeout_seconds: float = 30.0,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self.ocr_allowed = ocr_allowed
        self.ocr_max_pages = ocr_max_pages
        self.ocr_timeout_seconds = ocr_timeout_seconds
        host = urlparse(self.base_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=24_000_000,
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
        return self.config.tjrs_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        if not any([query.text, query.exact_phrase, query.number]):
            raise ValueError("TJRS jurisprudence search requires text, exact_phrase or number")
        _validate_degree_scope(query)
        endpoint = "/buscas/jurisprudencia/ajax.php"
        params = build_tjrs_search_parameters(query)
        form = {
            "action": "consultas_solr_ajax",
            "metodo": "buscar_resultados",
            "parametros": _encode_nested_parameters(params),
        }
        data, source_url = self._request_json(endpoint, data=form)
        page_size = _page_size(query.page_size)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={
                "text": query.text,
                "number": query.number,
                "page": query.page,
                "page_size": page_size,
                "body_contract": "tjrs_solr_ajax_v1",
            },
            source_url=source_url,
            limitations=[
                "A resposta declara content-type legado text/html, mas o corpo e JSON.",
                "O parser decodifica o envelope SOLR e preserva facets/highlighting.",
                "A rota publica retorna TIFF base64; a extracao textual/OCR permanece "
                "explicita como indisponivel.",
            ],
            **self._last_http_metadata,
        )
        return parse_tjrs_search_response(data, query=query, trace=trace)

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document = self.get_document(precedent_id)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[],
            source_trace=document.source_trace,
            raw={
                "document_id": precedent_id,
                "document_type": document.content_type,
                "raw_content_sha256": document.sha256,
                "raw_content_bytes": document.byte_size,
                "extraction_status": document.extraction_status.value,
            },
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Fetch the official TIFF exposed by the public ``retorna_tiff`` route."""

        normalized_id = document_id.removeprefix("tjrs-solr-")
        endpoint = "/buscas/jurisprudencia/ajax.php"
        payload = {
            "action": "consultas_solr_ajax",
            "metodo": "retorna_tiff",
            "codigo_documento": normalized_id,
        }
        data, source_url = self._request_json(endpoint, data=payload)
        encoded = data.get("documento")
        if not isinstance(encoded, str) or not encoded.strip():
            raise ParserContractChangedError("TJRS detail response missing documento TIFF")
        try:
            content = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            raise ParserContractChangedError(
                "TJRS detail response contains invalid base64"
            ) from exc
        if not content or not content.startswith((b"II*\x00", b"MM\x00*")):
            raise ParserContractChangedError("TJRS detail response is not a TIFF document")
        if len(content) > 20_000_000:
            raise SourceUnavailableError("TJRS detail TIFF exceeds the provider size limit")
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=payload,
            source_url=source_url,
            limitations=[
                "A fonte entrega o inteiro teor como TIFF base64; OCR nao e inferido "
                "nem executado automaticamente.",
                "O conteudo binario original permanece preservado para processamento "
                "posterior permitido.",
            ],
            **self._last_http_metadata,
            transformations=["base64_decoded", "tiff_magic_validated"],
        )
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="inteiro_teor_tiff",
            content=content,
            content_type="image/tiff",
            title=f"TJRS inteiro teor {normalized_id}",
            url=source_url,
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"codigo_documento": normalized_id, "transport": "json_base64"},
            parser="tjrs_solr.retorna_tiff",
            ocr_allowed=self.ocr_allowed,
            ocr_max_pages=self.ocr_max_pages,
            ocr_timeout_seconds=self.ocr_timeout_seconds,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJRS Jurisprudencia AJAX/SOLR",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "facets", "pagination"],
            document_types=["acordao", "decisao", "informativo", "inteiro_teor_tiff"],
            content_formats=["json", "tiff"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "id",
                "case_number",
                "decision_type",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "document_url",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /buscas/jurisprudencia/",
                "POST /buscas/jurisprudencia/ajax.php",
            ],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_live_tests=True,
            pagination_mode="offset",
            completeness_contract="reported_total_and_offset_window",
            # The public document endpoint is exposed as an explicit detail
            # call.  Keep the capability vocabulary aligned with the shared
            # contract so callers can discover it like other detail routes.
            full_text_access="detail_call",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "page",
                "published_from",
                "published_to",
            ],
            unsupported_filters=[
                "types",
                "oab",
                "courts",
                "all_words",
                "any_words",
                "without_words",
                "rapporteur",
                "updated_from",
                "updated_to",
                "case_class",
                "judging_body",
                "decision_type",
                "judgment_date_from",
                "judgment_date_to",
                "lawyer_name",
                "legal_area",
                "party_document",
                "party_name",
                "police_document",
                "precatory_number",
                "cda",
                "source_origin",
                "source_origins",
                "fetch_details",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "translated",
                "number": "translated",
                "page": "native",
                "published_from": "translated",
                "published_to": "translated",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "types": "unsupported",
                "oab": "unsupported",
                "courts": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "rapporteur": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "decision_type": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
                "lawyer_name": "unsupported",
                "legal_area": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "cda": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
                "fetch_details": "unsupported",
            },
            limitations=[
                "O backend retorna no maximo o page size solicitado pelo frontend.",
                "Facets sao preservadas sem serem tratadas como campos canonicos de decisao.",
                "Facets de tipo e OAB observadas no indice nao sao filtros runtime promovidos.",
                "O inteiro teor e preservado como TIFF; OCR somente com ocr_allowed=True "
                "e os extras nanojuris[ocr].",
            ],
            responsible_use=[
                "Usar termos especificos, page_size pequeno e rate limit.",
                "Preservar o charset ISO-8859-1 declarado pela fonte.",
                "Nao interpretar numFound como garantia de coleta integral.",
            ],
        )

    def _request_json(self, endpoint: str, **kwargs: Any) -> tuple[dict[str, Any], str]:
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": self.config.user_agent,
            **kwargs.pop("headers", {}),
        }
        request = TransportRequest(
            source=self.name,
            operation="solr_ajax_request",
            method="POST",
            url=url,
            headers=headers,
            params=kwargs.pop("params", {}),
            data=kwargs.pop("data", None),
            json_body=kwargs.pop("json", None),
            idempotent=False,
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJRS jurisprudence request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJRS transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJRS transport returned no HTTP status")
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
            raise RateLimitDetectedError("TJRS jurisprudence returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError("TJRS jurisprudence requires access validation")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJRS jurisprudence returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(
                f"TJRS jurisprudence rejected request with HTTP {status_code}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJRS jurisprudence response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJRS jurisprudence JSON root is not an object")
        return data, str(response.final_url or url)


def build_tjrs_search_parameters(query: JurisprudenceQuery) -> dict[str, str | int]:
    """Build the nested query string consumed by the TJRS AJAX endpoint."""

    term = query.text or query.exact_phrase or query.number
    parameters: dict[str, str | int] = {
        "aba": "jurisprudencia",
        "realizando_pesquisa": 1,
        "pagina_atual": max(query.page, 1),
        "q_palavra_chave": term,
        "conteudo_busca": "ementa_completa",
    }
    if query.published_from:
        parameters["data_publicacao_inicio"] = query.published_from
    if query.published_to:
        parameters["data_publicacao_fim"] = query.published_to
    return parameters


def _encode_nested_parameters(parameters: dict[str, str | int]) -> str:
    """Encode the inner query while preserving its ampersand separators."""

    return "&".join(f"{key}={quote_plus(str(value))}" for key, value in parameters.items())


def parse_tjrs_search_response(
    data: dict[str, Any], *, query: JurisprudenceQuery, trace: SourceTrace
) -> SearchPage:
    """Parse the Solr-like TJRS response envelope."""

    response = data.get("response")
    if not isinstance(response, dict):
        raise ParserContractChangedError("TJRS response missing response object")
    docs = response.get("docs")
    if not isinstance(docs, list):
        raise ParserContractChangedError("TJRS response missing response.docs list")
    page_size = _page_size(query.page_size)
    results = [
        _doc_to_result(item, trace=trace) for item in docs[:page_size] if isinstance(item, dict)
    ]
    start_index = _as_int(response.get("start"), default=(max(query.page, 1) - 1) * page_size)
    total = _as_int(response.get("numFound"), default=len(results))
    start = start_index + 1 if results else 0
    complete, completeness_reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        total_is_authoritative="numFound" in response,
    )
    return SearchPage(
        source="tjrs_solr",
        total=total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=max(query.page, 1),
        page_size=page_size,
        results=results,
        aggregations={
            "facets": data.get("facets") if isinstance(data.get("facets"), list) else [],
            "facet_counts": data.get("facet_counts")
            if isinstance(data.get("facet_counts"), dict)
            else {},
            "highlighting": data.get("highlighting")
            if isinstance(data.get("highlighting"), dict)
            else {},
        },
        source_trace=trace,
        pagination_mode="offset",
        is_complete=complete,
        completeness_reason=completeness_reason,
        total_known="numFound" in response,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY,
    )


def _doc_to_result(item: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    external_id = _first(item, "cod_ementa", "numero_processo", "_version_")
    if not external_id:
        raise ParserContractChangedError("TJRS document missing stable identifier")
    summary = _first(item, "ementa_completa", "ementa_text", "ementa")
    document_reference = _first(item, "documento_tiff")
    document_url = (
        document_reference if document_reference.startswith(("http://", "https://")) else None
    )
    decision_type = _first(item, "tipo_documento", "tipo_processo") or "jurisprudencia"
    document_type = _normalize_document_type(decision_type)
    if document_type == "sentenca":
        raise ParserContractChangedError("TJRS CJSG returned a first-degree sentence")
    return JurisprudenceResult(
        id=f"tjrs-solr-{external_id}",
        source="tjrs_solr",
        court=_first(item, "nome_tribunal", "origem") or "TJRS",
        type=decision_type,
        number=_first(item, "numero_processo"),
        summary=summary or None,
        rapporteur=_first(item, "nome_relator", "relator_redator") or None,
        updated_at=_first(item, "data_atualizacao") or None,
        judgment_date=normalize_date_value(_first(item, "data_julgamento")) or None,
        publication_date=normalize_date_value(_first(item, "data_publicacao")) or None,
        degree="second",
        instance="second",
        branch="state",
        authority="TJRS",
        collection="CJSG",
        document_type=document_type,
        source_origin=_first(item, "origem", "nome_tribunal") or "TJRS",
        document_url=document_url,
        access_status=AccessStatus.PUBLIC,
        source_trace=trace,
        raw={
            **item,
            "orgao_julgador": _first(item, "orgao_julgador"),
            "document_url": document_url,
            "document_reference": document_reference or None,
            "degree": "second",
            "instance": "second",
            "branch": "state",
            "authority": "TJRS",
            "collection": "CJSG",
            "document_type": document_type,
        },
        field_provenance={
            "degree": {"source": "source_contract:tjrs_solr_acordaos"},
            "instance": {"source": "source_contract:tjrs_solr_acordaos"},
            "branch": {"source": "source_contract:tjrs"},
            "authority": {"source": "source_contract:tjrs"},
            "collection": {"source": "source_contract:tjrs_solr_acordaos"},
        },
    )


def _validate_degree_scope(query: JurisprudenceQuery) -> None:
    values = {value.strip().casefold() for value in query.types}
    if values & {"sentenca", "sentença", "first", "primeiro", "primeiro_grau"}:
        raise QueryRejectedError("TJRS jurisprudencia public exposes only second-degree decisions")


def _normalize_document_type(value: str) -> str:
    normalized = value.casefold()
    normalized = normalized.replace("ã", "a").replace("á", "a").replace("ç", "c")
    if "acord" in normalized:
        return "acordao"
    if "monocrat" in normalized:
        return "decisao_monocratica"
    if "sentenc" in normalized:
        return "sentenca"
    return "decisao"


def _first(item: dict[str, Any], *keys: str) -> str:
    """Return the first non-empty value, unwrapping Solr multi-valued fields.

    The live Solr response returns text fields such as ``ementa_completa`` as a
    single-element list. ``str([...])`` would leak the Python list repr into the
    canonical summary, so lists are flattened to their first non-empty member.
    """

    for key in keys:
        value = item.get(key)
        if isinstance(value, (list, tuple)):
            value = next(
                (member for member in value if member is not None and str(member).strip()),
                None,
            )
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _as_int(value: object, *, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 50))
