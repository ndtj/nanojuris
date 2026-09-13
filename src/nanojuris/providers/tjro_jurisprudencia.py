"""TJRO public jurisprudence search adapter (JURIS Elasticsearch API).

The endpoint is public and has a bounded, reproducible minimum contract for
textual search.  Filters whose vocabulary is not confirmed remain explicit
warnings/validation gaps; they are never silently translated or treated as
zero results.
"""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata
from datetime import datetime
from typing import Any
from urllib.parse import quote, urljoin, urlparse

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
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

TJRO_JURISPRUDENCIA_ENDPOINT = "/search/varios_parametros/"
TJRO_RELATED_DOCUMENTS_ENDPOINT = "/search/documentos_relacionados/"
TJRO_DEFAULT_PAGE_SIZE = 10
TJRO_MAX_PAGE_SIZE = 100


class TjroJurisprudenciaProvider(JurisprudenceProvider):
    """Adapter for the TJRO general textual jurisprudence API."""

    name = "tjro_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tjro_jurisprudencia_url).hostname
        self.http = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,) if host else (),
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
        return self.config.tjro_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        payload = build_tjro_payload(query)
        data, source_url = self._request_json(payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"POST {TJRO_JURISPRUDENCIA_ENDPOINT}",
            query={
                "text": query.text,
                "exact_phrase": query.exact_phrase,
                "number": query.number,
                "rapporteur": query.rapporteur,
                "updated_from": query.updated_from,
                "updated_to": query.updated_to,
                "page": query.page,
                "page_size": query.page_size,
                "filters": {
                    "tipo": "omitted_by_contract",
                    "grau_jurisdicao": payload.get("fields", {}).get(
                        "grau_jurisdicao", "not_requested"
                    ),
                },
            },
            source_url=source_url,
            limitations=[
                "A fonte publica um endpoint Elasticsearch sujeito a mudancas de schema.",
                "O vocabulario do filtro tipo ainda nao foi confirmado e nao e enviado.",
                "O inteiro teor e obtido por rota publica separada quando solicitado.",
                "A rota de documento exige cabecalhos de navegador (Origin/Referer), "
                "sem credenciais ou bypass de controle de acesso.",
                "O provider nao contorna CAPTCHA, WAF, login ou limites.",
            ],
            **self._last_http_metadata,
        )
        page = parse_tjro_response(data, query=query, trace=trace)
        if query.fetch_details:
            for result in page.results:
                # ``_id`` is a stable search-result identifier and, on the
                # live PJEPG/PJESG index, already contains the source suffix
                # (for example ``137613154-PJEPG``).  The document route,
                # however, expects the numeric ``id_processo_documento`` and
                # the origin as two separate path components.  Prefer the
                # explicit document id captured by the parser and fall back
                # to the canonical result id for older fixtures.
                native_id = _string(result.raw.get("document_native_id")) or _string(
                    result.raw.get("native_id")
                )
                source_origin = _string(result.raw.get("sistema_origem")) or _string(
                    result.raw.get("source_system")
                )
                document_id = (
                    f"{native_id}-{source_origin}" if native_id and source_origin else result.id
                )
                document = self.get_document(document_id)
                result.full_text = document.text
                result.raw["full_text"] = document.text
                result.raw["full_text_status"] = "loaded" if document.text else "empty"
                result.raw["document_content_type"] = document.content_type
                result.raw["content_sha256"] = document.sha256
                result.raw["response_bytes"] = document.byte_size
                result.raw["document_url"] = document.url or result.raw.get("document_url")
                result.extraction_status = document.extraction_status
        return page

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        """Return the public TJRO inteiro teor as a decision bundle."""

        document = self.get_document(precedent_id)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document.text or "",
                    "content_type": document.content_type or "application/octet-stream",
                    "source_content_type": document.raw_metadata.get("source_content_type"),
                }
            ],
            source_trace=document.source_trace,
            raw={"document_id": precedent_id, **document.raw_metadata},
            raw_bytes=document.raw_bytes,
        )

    def _request(
        self,
        *,
        operation: str,
        method: str,
        url: str,
        headers: dict[str, str],
        json_body: Any = None,
    ):
        request = TransportRequest(
            source=self.name,
            operation=operation,
            method=method,
            url=url,
            headers=headers,
            json_body=json_body,
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        try:
            response = self.http.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJRO request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJRO transport failed: {response.error_type or response.status.value}"
            )
        return response

    def get_related_documents(self, principal_id: str) -> SearchPage:
        """Return the PJESG documents linked to one principal document.

        The official frontend calls this route only for PJESG records that
        expose ``id_documento_principal``.  It is deliberately a separate
        operation: a normal search must not issue an unbounded fan-out of
        related-document requests.
        """

        normalized_id = _validate_related_document_id(principal_id)
        endpoint = f"{TJRO_RELATED_DOCUMENTS_ENDPOINT}{quote(normalized_id, safe='')}"
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        response = self._request(
            operation="tjro_related_documents",
            method="GET",
            url=url,
            headers={
                "Accept": "application/json,*/*",
                "Origin": "https://juris.tjro.jus.br",
                "Referer": "https://juris.tjro.jus.br/jurisprudencia/",
            },
        )
        content = bytes(response.body)
        headers = response.headers
        response_url = _safe_url(str(response.final_url or url))
        status = response.status_code
        if status is None:
            raise SourceUnavailableError("TJRO related-documents response had no HTTP status")
        self._last_http_metadata = {
            "http_status": status,
            "final_url": response_url,
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if status < 400 else "error",
        }
        if status == 429:
            raise RateLimitDetectedError("TJRO related-documents route returned HTTP 429")
        if status in {401, 403, 420}:
            raise AccessControlRequiredError(
                f"TJRO related-documents route rejected HTTP {status}; access validation required"
            )
        if status in {400, 422}:
            raise QueryRejectedError(f"TJRO related-documents route rejected HTTP {status}")
        if status >= 500:
            raise SourceUnavailableError(f"TJRO related-documents route returned HTTP {status}")
        if status >= 400:
            raise SourceUnavailableError(f"TJRO related-documents route returned HTTP {status}")
        try:
            data = response.json()
        except (TypeError, ValueError) as exc:
            raise ParserContractChangedError("TJRO related-documents response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJRO related-documents JSON root is not an object")
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"GET {endpoint}",
            query={"id_documento_principal": normalized_id},
            source_url=response_url,
            limitations=[
                "Rota condicional publica observada no frontend para documentos PJESG.",
                "A chamada e feita apenas sob demanda para um id principal explicito.",
            ],
            **self._last_http_metadata,
        )
        return parse_tjro_related_response(data, principal_id=normalized_id, trace=trace)

    def get_document(self, document_id: str, *, extension: str = "pdf") -> CanonicalDocument:
        """Download one public TJRO document while preserving source bytes.

        ``document_id`` is the canonical result id (for example
        ``tjro-jurisprudencia-137613154-PJEPG``) or the native
        ``id_processo_documento-sistema_origem`` value observed in a hit.
        The official frontend exposes only ``pdf`` and ``docx`` extensions.
        """

        native_id, source_origin = _parse_document_id(document_id)
        normalized_extension = extension.strip().lower().lstrip(".")
        if normalized_extension not in {"pdf", "docx"}:
            raise ValueError("TJRO document extension must be pdf or docx")
        endpoint = (
            "/pje/buscar_pdf_ou_docx/"
            f"{quote(source_origin, safe='')}/{quote(native_id, safe='')}/"
            f"{normalized_extension}/"
        )
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        response = self._request(
            operation="tjro_document",
            method="GET",
            url=url,
            headers={
                # The TJRO edge rejects a comma-separated list of long
                # vendor media types with HTTP 420.  A browser-compatible
                # primary type plus wildcard is accepted for both formats.
                "Accept": (
                    "application/pdf,*/*"
                    if normalized_extension == "pdf"
                    else (
                        "application/vnd.openxmlformats-officedocument."
                        "wordprocessingml.document,*/*"
                    )
                ),
                "Origin": "https://juris.tjro.jus.br",
                "Referer": "https://juris.tjro.jus.br/jurisprudencia/",
            },
        )
        content = bytes(response.body)
        headers = response.headers
        response_url = _safe_url(str(response.final_url or url))
        content_type = headers.get("Content-Type") or headers.get("content-type")
        status = response.status_code
        if status is None:
            raise SourceUnavailableError("TJRO document response had no HTTP status")
        self._last_http_metadata = {
            "http_status": status,
            "final_url": response_url,
            "content_type": content_type,
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if status < 400 else "error",
        }
        if status == 429:
            raise RateLimitDetectedError("TJRO document route returned HTTP 429")
        if status in {401, 403, 420}:
            raise AccessControlRequiredError(
                f"TJRO document route rejected HTTP {status}; access validation required"
            )
        if status in {400, 422}:
            raise QueryRejectedError(f"TJRO document route rejected HTTP {status}")
        if status >= 500:
            raise SourceUnavailableError(f"TJRO document route returned HTTP {status}")
        if status >= 400:
            raise SourceUnavailableError(f"TJRO document route returned HTTP {status}")
        if not content:
            raise ParserContractChangedError("TJRO document response is empty")
        if _looks_like_html_error(content, content_type):
            raise ParserContractChangedError(
                "TJRO document route returned HTML instead of the requested document"
            )
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"GET {endpoint}",
            query={
                "document_id": document_id,
                "native_id": native_id,
                "sistema_origem": source_origin,
                "extension": normalized_extension,
            },
            source_url=response_url,
            limitations=[
                "Inteiro teor publico entregue pela rota oficial buscar_pdf_ou_docx.",
                "A chamada usa cabecalhos de navegador exigidos pela superficie publica; "
                "nenhuma credencial ou contorno de acesso e utilizado.",
            ],
            **self._last_http_metadata,
        )
        return build_canonical_document(
            document_id=f"tjro-jurisprudencia-document-{native_id}-{source_origin}",
            source=self.name,
            document_type="inteiro_teor",
            content=content,
            content_type=content_type,
            title=f"TJRO JURIS inteiro teor {native_id}",
            url=response_url,
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={
                "native_id": native_id,
                "sistema_origem": source_origin,
                "extension": normalized_extension,
                "source_content_type": content_type,
                "content_disposition": headers.get("Content-Disposition")
                or headers.get("content-disposition"),
            },
            parser="tjro_jurisprudencia.get_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJRO Jurisprudencia textual",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "case_number", "date_range", "rapporteur", "pagination"],
            document_types=["decision", "sentence", "vote", "acordao"],
            content_formats=["json", "html", "text", "pdf", "docx"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "subject",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "full_text",
                "document_url",
                "full_text_url",
                "degree",
                "source_system",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                f"POST {TJRO_JURISPRUDENCIA_ENDPOINT}",
                "GET /search/documentos_relacionados/<id_documento_principal>",
                "GET /pje/buscar_pdf_ou_docx/<sistema>/<id>/<pdf|docx>/",
            ],
            supports_full_text=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            supports_cli=False,
            supports_unified_search=True,
            supports_mcp=False,
            supports_studio=False,
            pagination_mode="offset",
            max_remote_page=None,
            max_remote_page_size=None,
            completeness_contract="hits.total.value with offset window",
            full_text_access="detail_call",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "rapporteur",
                "updated_from",
                "updated_to",
                "fetch_details",
            ],
            unsupported_filters=[
                "courts",
                "party_name",
                "party_document",
                "lawyer_name",
                "oab",
                "precatory_number",
                "police_document",
                "cda",
                "legal_area",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "translated",
                "number": "native",
                "rapporteur": "native",
                "updated_from": "native",
                "updated_to": "native",
                "fetch_details": "translated",
                "types": "local_postfilter",
                "published_from": "local_postfilter",
                "published_to": "local_postfilter",
                "all_words": "local_postfilter",
                "any_words": "local_postfilter",
                "without_words": "local_postfilter",
                "source_origin": "local_postfilter",
                "source_origins": "local_postfilter",
                "case_class": "local_postfilter",
                "judging_body": "local_postfilter",
                "degree": "translated",
                "instance": "translated",
                "branch": "local_postfilter",
                "authority": "local_postfilter",
                "collection": "local_postfilter",
                "document_type": "local_postfilter",
                "decision_type": "local_postfilter",
                "judgment_date_from": "local_postfilter",
                "judgment_date_to": "local_postfilter",
            },
            ordering_modes=["relevance_then_judgment_date"],
            detail_modes=["pdf_or_docx_download"],
            limitations=[
                "A federacao padrao usa somente o contrato minimo de busca textual.",
                "O limite maximo remoto de size ainda nao foi confirmado; o adapter "
                "mantem limite local de 100 para chamadas bounded.",
                "O vocabulario do filtro tipo e de classe permanece pendente de contrato.",
                "Grau de jurisdicao foi observado no transporte, mas ainda nao faz "
                "parte do modelo canonico de filtros.",
            ],
            responsible_use=[
                "Usar somente a superficie publica e chamadas bounded.",
                "Preservar o hit original em raw e a origem em SourceTrace.",
                "Nao tratar filtro divergente ou falha externa como zero de acervo.",
            ],
        )

    def _request_json(self, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
        url = self.base_url + TJRO_JURISPRUDENCIA_ENDPOINT
        response = self._request(
            operation="tjro_jurisprudence_search",
            method="POST",
            url=url,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json_body=payload,
        )
        content = bytes(response.body)
        headers = response.headers
        response_url = _safe_url(str(response.final_url or url))
        status = response.status_code
        if status is None:
            raise SourceUnavailableError("TJRO jurisprudence response had no HTTP status")
        self._last_http_metadata = {
            "http_status": status,
            "final_url": response_url,
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if status < 400 else "error",
        }
        if status == 429:
            raise RateLimitDetectedError("TJRO jurisprudence returned HTTP 429")
        if status in {401, 403}:
            raise AccessControlRequiredError("TJRO jurisprudence requires access validation")
        if status in {400, 422}:
            raise QueryRejectedError(f"TJRO jurisprudence rejected HTTP {status}")
        if status >= 500:
            raise SourceUnavailableError(f"TJRO jurisprudence returned HTTP {status}")
        if status >= 400:
            raise SourceUnavailableError(f"TJRO jurisprudence returned HTTP {status}")
        try:
            data = response.json()
        except (TypeError, ValueError) as exc:
            raise ParserContractChangedError("TJRO jurisprudence response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJRO jurisprudence JSON root is not an object")
        return data, response_url


def build_tjro_payload(
    query: JurisprudenceQuery, *, page_size: int | None = None
) -> dict[str, Any]:
    """Build the confirmed public payload without the divergent ``tipo`` filter."""

    _validate_query(query)
    size = page_size if page_size is not None else query.page_size
    if size < 1 or size > TJRO_MAX_PAGE_SIZE:
        raise ValueError(f"page_size deve estar entre 1 e {TJRO_MAX_PAGE_SIZE}")
    fields: dict[str, Any] = {}
    search_term = _search_term(query)
    if search_term:
        fields["query"] = search_term
    if query.number.strip():
        fields["nr_processo"] = query.number.strip()
    if query.rapporteur.strip():
        fields["ds_nome"] = query.rapporteur.strip()
    if query.updated_from.strip():
        fields["dtjulgamento_inicio"] = query.updated_from.strip()
    if query.updated_to.strip():
        fields["dtjulgamento_fim"] = query.updated_to.strip()
    # The public frontend sends the degree selector as a list under
    # ``fields.grau_jurisdicao``. Keep it remote so a CJSG query does not
    # inspect only the default first-degree window and report a false empty.
    degree_filter = _normalize_degree_filter(query.degree or query.instance)
    if not degree_filter and _fold(query.collection) == "cjsg":
        degree_filter = "second"
    if degree_filter in {"first", "second"}:
        fields["grau_jurisdicao"] = [1 if degree_filter == "first" else 2]
    return {
        "from": (query.page - 1) * size,
        "size": size,
        "fields": fields,
        "sort": [{"_score": "desc"}, {"dtjulgamento": "desc"}],
        "token": "",
        "highlight": {
            "type": "plain",
            "number_of_fragments": 1,
            "fragment_size": 3000,
            "require_field_match": "true",
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"],
            "fields": [{"ds_modelo_documento": {"number_of_fragments": 1}}],
        },
    }


def parse_tjro_response(
    data: dict[str, Any], *, query: JurisprudenceQuery, trace: SourceTrace
) -> SearchPage:
    """Parse a TJRO JURIS response into normalized results."""

    hits_root = data.get("hits")
    if not isinstance(hits_root, dict):
        raise ParserContractChangedError("TJRO response missing hits object")
    raw_total = hits_root.get("total")
    total = _parse_total(raw_total)
    raw_hits = hits_root.get("hits")
    if not isinstance(raw_hits, list):
        raise ParserContractChangedError("TJRO response missing hits.hits list")
    results: list[JurisprudenceResult] = []
    for index, hit in enumerate(raw_hits):
        if not isinstance(hit, dict):
            raise ParserContractChangedError(f"TJRO hit {index} is not an object")
        results.append(_parse_hit(hit, trace=trace, query=query))
    local_filter_names = _local_filter_names(query)
    if local_filter_names:
        results = [result for result in results if _matches_local_filters(result, query)]
    results = results[: query.page_size]
    start = (query.page - 1) * query.page_size + 1 if results else 0
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        total_is_authoritative=True,
    )
    if local_filter_names:
        # The remote total describes the unfiltered window.  Once a local
        # refinement is applied, the adapter cannot claim source-level
        # completeness without fetching all remote pages, so keep the total
        # for diagnostics but explicitly mark the page partial.
        complete = False
        reason = (
            reason or ""
        ) + " Filtros locais aplicados; total remoto refere-se à janela original."
    return SearchPage(
        source="tjro_jurisprudencia",
        total=total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=query.page,
        page_size=query.page_size,
        results=results,
        source_trace=trace,
        pagination_mode="offset",
        is_complete=complete,
        completeness_reason=reason,
        ordering="relevance_then_judgment_date",
        filters_applied={
            "tipo": "omitted",
            **{name: "local_postfilter" for name in local_filter_names},
        },
        total_known=True,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY,
    )


def parse_tjro_related_response(
    data: dict[str, Any], *, principal_id: str, trace: SourceTrace
) -> SearchPage:
    """Parse the PJESG related-document envelope without losing source data."""

    hits_root = data.get("hits")
    if not isinstance(hits_root, dict):
        raise ParserContractChangedError("TJRO related-documents response missing hits object")
    total = _parse_total(hits_root.get("total"))
    raw_hits = hits_root.get("hits")
    if not isinstance(raw_hits, list):
        raise ParserContractChangedError("TJRO related-documents response missing hits.hits list")
    query = JurisprudenceQuery(text=f"related:{principal_id}", page_size=max(len(raw_hits), 1))
    results: list[JurisprudenceResult] = []
    for index, hit in enumerate(raw_hits):
        if not isinstance(hit, dict):
            raise ParserContractChangedError(f"TJRO related-documents hit {index} is not an object")
        result = _parse_hit(hit, trace=trace, query=query)
        result.raw["related_to"] = principal_id
        results.append(result)
    complete, reason = page_completeness(
        reported_total=total,
        start=1 if results else 0,
        returned=len(results),
        total_is_authoritative=True,
    )
    return SearchPage(
        source="tjro_jurisprudencia",
        total=total,
        start=1 if results else 0,
        end=len(results) if results else 0,
        page=1,
        page_size=max(len(results), 1),
        results=results,
        source_trace=trace,
        pagination_mode="single_response",
        is_complete=complete,
        completeness_reason=reason,
        ordering="source_order",
        filters_applied={"related_to": principal_id},
        total_known=True,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY,
    )


def _parse_hit(
    hit: dict[str, Any], *, trace: SourceTrace, query: JurisprudenceQuery
) -> JurisprudenceResult:
    source = hit.get("_source")
    if not isinstance(source, dict):
        raise ParserContractChangedError("TJRO hit missing _source object")
    native_id = _string(hit.get("_id")) or _string(source.get("id_processo_documento"))
    if not native_id:
        native_id = _string(source.get("ds_md5_documento"))
    if not native_id:
        raise ParserContractChangedError("TJRO hit missing stable identifier")
    model_html = _string(source.get("ds_modelo_documento"))
    summary = _clean_html(model_html) or None
    highlight = hit.get("highlight")
    highlights = _parse_highlights(highlight)
    case_number_raw = _string(source.get("nr_processo"))
    judgment_raw = _string(source.get("dtjulgamento"))
    publication_raw = _string(source.get("dtpublicacao"))
    judgment_date = _date_value(judgment_raw)
    publication_date = _date_value(publication_raw)
    raw_source = dict(source)
    document_url = None
    source_origin = _string(source.get("sistema_origem"))
    decision_type = _decision_type(source.get("tipo"))
    degree_raw = source.get("grau_jurisdicao")
    degree = _normalize_degree(degree_raw, source_origin)
    judging_body = (
        _string(source.get("ds_orgao_julgador_colegiado"))
        or _string(source.get("ds_orgao_julgador"))
        or None
    )
    document_native_id = _string(source.get("id_processo_documento"))
    if source_origin and document_native_id and trace.source_url:
        source_base_url = trace.source_url.split("/search/", 1)[0]
        document_url = _document_url(source_base_url, source_origin, document_native_id)
    return JurisprudenceResult(
        id=f"tjro-jurisprudencia-{_safe_id(native_id)}",
        source="tjro_jurisprudencia",
        court="TJRO",
        type=decision_type,
        number=_format_case_number(case_number_raw) or None,
        summary=summary,
        rapporteur=(
            _string(source.get("ds_nome"))
            or _string(source.get("nome_relator_acordao"))
            or _string(source.get("nome_relator_processo"))
            or None
        ),
        updated_at=publication_date or judgment_date,
        judgment_date=judgment_date,
        publication_date=publication_date,
        source_updated_at=_date_value(_string(source.get("data_indexacao"))),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if summary else ExtractionStatus.PARTIAL,
        highlights=highlights,
        source_trace=trace,
        case_class=_string(source.get("ds_classe_judicial")) or None,
        judging_body=judging_body,
        degree=degree,
        instance=degree,
        branch="state",
        authority="TJRO",
        collection="JURISPRUDENCIA",
        document_type=decision_type,
        source_origin=source_origin or None,
        document_url=document_url,
        raw={
            "native_id": native_id,
            "document_native_id": document_native_id or None,
            "nr_processo": case_number_raw or None,
            "tipo": _string(source.get("tipo")) or None,
            "case_class": _string(source.get("ds_classe_judicial")) or None,
            "subject": _string(source.get("ds_assunto_trf")) or None,
            "judging_body": judging_body,
            "degree": degree_raw,
            "degree_canonical": degree,
            "instance_canonical": degree,
            "source_system": _string(source.get("sistema_origem")) or None,
            "sistema_origem": _string(source.get("sistema_origem")) or None,
            "judgment_date_raw": judgment_raw or None,
            "publication_date_raw": publication_raw or None,
            "highlight": highlight if isinstance(highlight, dict) else {},
            "source_sort": hit.get("sort") if isinstance(hit.get("sort"), list) else [],
            "document_url": document_url,
            "full_text_url": document_url,
            "source": raw_source,
            "query_page": query.page,
        },
    )


def _validate_query(query: JurisprudenceQuery) -> None:
    if not (query.text.strip() or query.exact_phrase.strip() or query.number.strip()):
        raise QueryRejectedError("TJRO exige texto, frase exata ou numero do processo")
    unsupported = {
        "courts": query.courts,
        "party_name": query.party_name,
        "party_document": query.party_document,
        "lawyer_name": query.lawyer_name,
        "oab": query.oab,
        "precatory_number": query.precatory_number,
        "police_document": query.police_document,
        "cda": query.cda,
        "legal_area": query.legal_area,
    }
    present = [name for name, value in unsupported.items() if value]
    if present:
        raise UnsupportedQueryError(
            "TJRO ainda nao confirmou estes filtros: " + ", ".join(sorted(present))
        )


_LOCAL_FILTER_FIELDS = frozenset(
    {
        "types",
        "all_words",
        "any_words",
        "without_words",
        "published_from",
        "published_to",
        "source_origin",
        "source_origins",
        "case_class",
        "judging_body",
        "degree",
        "instance",
        "branch",
        "authority",
        "collection",
        "document_type",
        "decision_type",
        "judgment_date_from",
        "judgment_date_to",
    }
)


def _local_filter_names(query: JurisprudenceQuery) -> list[str]:
    """Return refinements that are applied after the bounded TJRO request."""

    values: dict[str, Any] = {
        "types": query.types,
        "all_words": query.all_words,
        "any_words": query.any_words,
        "without_words": query.without_words,
        "published_from": query.published_from,
        "published_to": query.published_to,
        "source_origin": query.source_origin,
        "source_origins": query.source_origins,
        "case_class": query.case_class,
        "judging_body": query.judging_body,
        "degree": query.degree,
        "instance": query.instance,
        "branch": query.branch,
        "authority": query.authority,
        "collection": query.collection,
        "document_type": query.document_type,
        "decision_type": query.decision_type,
        "judgment_date_from": query.judgment_date_from,
        "judgment_date_to": query.judgment_date_to,
    }
    return sorted(name for name in _LOCAL_FILTER_FIELDS if _has_query_value(values[name]))


def _matches_local_filters(result: JurisprudenceResult, query: JurisprudenceQuery) -> bool:
    """Apply only fields present in the canonical TJRO result.

    This is intentionally a post-filter over the returned window.  The caller
    receives ``is_complete=False`` when it is used, so a narrow page is never
    presented as an exhaustive source result.
    """

    haystack = " ".join(
        str(value or "")
        for value in (
            result.summary,
            result.full_text,
            getattr(result, "case_number", None),
            result.number,
        )
    ).casefold()
    if query.all_words and not all(
        token.casefold() in haystack for token in query.all_words.split()
    ):
        return False
    if query.any_words and not any(
        token.casefold() in haystack for token in query.any_words.split()
    ):
        return False
    if query.without_words and any(
        token.casefold() in haystack for token in query.without_words.split()
    ):
        return False

    if query.types:
        accepted = {_fold(str(value)) for value in query.types}
        values = {_fold(str(value or "")) for value in (result.type, result.document_type)}
        if not accepted.intersection(values):
            return False
    if query.decision_type and _fold(query.decision_type) not in {
        _fold(str(result.type or "")),
        _fold(str(result.document_type or "")),
    }:
        return False

    for query_value, actual in (
        (query.case_class, result.case_class),
        (query.judging_body, result.judging_body),
        (query.branch, result.branch),
        (query.authority, result.authority),
        (query.document_type, result.document_type),
    ):
        if query_value and _fold(query_value) not in _fold(str(actual or "")):
            return False
    if query.collection:
        requested_collection = _fold(query.collection)
        actual_collection = _fold(str(result.collection or ""))
        # CJPG/CJSG are NanoJuris canonical scopes while TJRO labels the
        # native route simply JURISPRUDENCIA.  The degree field is the
        # authoritative discriminator for these aliases.
        if requested_collection == "cjsg":
            if result.degree != "second":
                return False
        elif requested_collection == "cjpg":
            if result.degree != "first":
                return False
        elif requested_collection not in actual_collection:
            return False
    if query.source_origin and _fold(query.source_origin) not in _fold(result.source_origin or ""):
        return False
    if query.source_origins:
        origins = {_fold(str(value)) for value in query.source_origins}
        if _fold(result.source_origin or "") not in origins:
            return False
    requested_degree = _normalize_degree_filter(query.degree or query.instance)
    if requested_degree and result.degree != requested_degree:
        return False
    if query.degree and query.instance:
        if _normalize_degree_filter(query.degree) != _normalize_degree_filter(query.instance):
            return False
    if not _date_between(result.publication_date, query.published_from, query.published_to):
        return False
    if not _date_between(result.judgment_date, query.judgment_date_from, query.judgment_date_to):
        return False
    return True


def _date_between(value: str | None, start: str, end: str) -> bool:
    if not (start or end):
        return True
    if not value:
        return False
    normalized = _date_value(value) or value[:10]
    lower = _date_value(start) if start else None
    upper = _date_value(end) if end else None
    return not (lower and normalized < lower) and not (upper and normalized > upper)


def _normalize_degree_filter(value: str) -> str | None:
    folded = _fold(value)
    if folded in {"1", "1g", "primeiro", "primeiro grau", "first", "first degree"}:
        return "first"
    if folded in {"2", "2g", "segundo", "segundo grau", "second", "second degree"}:
        return "second"
    if folded in {"recursal", "turma recursal"}:
        return "recursal"
    return folded or None


def _has_query_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def _search_term(query: JurisprudenceQuery) -> str:
    text = query.text.strip()
    exact = query.exact_phrase.strip()
    if text and exact:
        return f'{text} "{exact}"'
    return text or exact


def _parse_total(value: Any) -> int:
    if isinstance(value, dict):
        value = value.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ParserContractChangedError("TJRO hits.total.value ausente ou invalido")
    total = int(value)
    if total < 0:
        raise ParserContractChangedError("TJRO hits.total.value negativo")
    return total


def _parse_highlights(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    output: dict[str, str] = {}
    for key, fragments in value.items():
        if isinstance(fragments, list):
            text = " ".join(_clean_html(_string(item)) for item in fragments if _string(item))
        else:
            text = _clean_html(_string(fragments))
        if text:
            output[str(key)] = text
    return output


def _clean_html(value: str) -> str:
    if not value:
        return ""
    soup = BeautifulSoup(html.unescape(value), "html.parser")
    for node in soup.select("script, style, noscript"):
        node.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def _decision_type(value: Any) -> str:
    folded = _fold(_string(value))
    if "acord" in folded:
        return "acordao"
    if "sentenc" in folded:
        return "sentenca"
    if "voto" in folded:
        return "voto"
    if "decis" in folded:
        return "decisao"
    return folded.replace(" ", "_") or "decision"


def _normalize_degree(value: Any, source_origin: str) -> str | None:
    """Normalize PJEPG/PJESG and numeric degree labels without guessing."""

    text = _fold(_string(value))
    origin = _fold(source_origin)
    if text in {"1", "1o", "primeiro", "primeiro grau", "first", "first degree"}:
        return "first"
    if text in {"2", "2o", "segundo", "segundo grau", "second", "second degree"}:
        return "second"
    if "epg" in origin or origin.endswith("1g"):
        return "first"
    if "esg" in origin or origin.endswith("2g"):
        return "second"
    if "recurs" in text:
        return "recursal"
    if "superior" in text:
        return "superior"
    return "unknown" if text or origin else None


def _date_value(value: str) -> str | None:
    text = value.strip()
    if not text:
        return None
    for pattern in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:19], pattern).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text[:10]


def _format_case_number(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) == 20:
        return (
            f"{digits[:7]}-{digits[7:9]}.{digits[9:13]}.{digits[13]}."
            f"{digits[14:16]}.{digits[16:20]}"
        )
    return value.strip()


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:-]+", "-", value).strip("-") or "unknown"


def _safe_url(value: str) -> str:
    return re.sub(r"([?&](?:token|access_token|authorization)=[^&]+)", "", value, flags=re.I)


def _parse_document_id(value: str) -> tuple[str, str]:
    raw = value.strip()
    if raw.startswith("tjro-jurisprudencia-"):
        raw = raw.removeprefix("tjro-jurisprudencia-")
    if "-" not in raw:
        raise ValueError("TJRO document_id must contain id_processo_documento and sistema_origem")
    native_id, source_origin = raw.rsplit("-", 1)
    if not native_id or not source_origin:
        raise ValueError("TJRO document_id has an invalid native id or source origin")
    if not re.fullmatch(r"[A-Za-z0-9_.:]+", native_id):
        raise ValueError("TJRO document_id contains invalid native id characters")
    if not re.fullmatch(r"[A-Za-z0-9_.:]+", source_origin):
        raise ValueError("TJRO document_id contains invalid source origin characters")
    return native_id, source_origin


def _validate_related_document_id(value: str) -> str:
    normalized = value.strip()
    if not normalized or not re.fullmatch(r"[A-Za-z0-9_.:]+", normalized):
        raise ValueError("TJRO principal document id contains invalid characters")
    return normalized


def _document_url(base_url: str, source_origin: str, native_id: str) -> str:
    return urljoin(
        base_url.rstrip("/") + "/",
        (
            "pje/buscar_pdf_ou_docx/"
            f"{quote(source_origin, safe='')}/{quote(native_id, safe='')}/pdf/"
        ),
    )


def _looks_like_html_error(content: bytes, content_type: str | None) -> bool:
    if "html" in str(content_type or "").lower():
        return True
    prefix = content[:4096].lstrip().lower()
    return prefix.startswith((b"<html", b"<!doctype html", b"<head", b"<title"))


def _string(value: Any) -> str:
    return (
        value.strip() if isinstance(value, str) else str(value).strip() if value is not None else ""
    )


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).casefold()
