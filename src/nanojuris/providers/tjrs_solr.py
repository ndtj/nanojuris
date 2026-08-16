"""TJRS public AJAX/SOLR jurisprudence provider."""

from __future__ import annotations

import hashlib
import time
from typing import Any
from urllib.parse import quote_plus, urljoin

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
    DecisionBundle,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider


class TjrsSolrProvider(JurisprudenceProvider):
    """Provider for the public TJRS jurisprudence AJAX endpoint."""

    name = "tjrs_solr"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0
        self._last_http_metadata: dict[str, Any] = {}

    @property
    def base_url(self) -> str:
        return self.config.tjrs_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        if not any([query.text, query.exact_phrase, query.number]):
            raise ValueError("TJRS jurisprudence search requires text, exact_phrase or number")
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
                "Rotas de detalhe e inteiro teor ainda nao foram promovidas.",
            ],
            **self._last_http_metadata,
        )
        return parse_tjrs_search_response(data, query=query, trace=trace)

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise NotImplementedError(
            "TJRS possui busca SOLR publica, mas a rota de detalhe/inteiro teor ainda nao "
            "tem contrato estavel no provider."
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJRS Jurisprudencia AJAX/SOLR",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "facets", "pagination"],
            document_types=["acordao", "decisao", "informativo"],
            content_formats=["json"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
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
            supports_full_text=False,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_live_tests=True,
            pagination_mode="offset",
            completeness_contract="reported_total_and_offset_window",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "page",
                "published_from",
                "published_to",
            ],
            limitations=[
                "O backend retorna no maximo o page size solicitado pelo frontend.",
                "Facets sao preservadas sem serem tratadas como campos canonicos de decisao.",
                "Detalhe e inteiro teor ainda precisam de rota publica validada.",
            ],
            responsible_use=[
                "Usar termos especificos, page_size pequeno e rate limit.",
                "Preservar o charset ISO-8859-1 declarado pela fonte.",
                "Nao interpretar numFound como garantia de coleta integral.",
            ],
        )

    def _request_json(self, endpoint: str, **kwargs: Any) -> tuple[dict[str, Any], str]:
        self._respect_rate_limit()
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        try:
            response = self.session.request(
                "POST",
                url,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "User-Agent": self.config.user_agent,
                },
                timeout=self.config.timeout,
                allow_redirects=True,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJRS jurisprudence request failed: {exc}") from exc
        content = bytes(getattr(response, "content", b"") or response.text.encode("utf-8"))
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": getattr(response, "url", url),
            "content_type": response.headers.get("Content-Type")
            if hasattr(response, "headers")
            else None,
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        if response.status_code == 429:
            raise RateLimitDetectedError("TJRS jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJRS jurisprudence requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJRS jurisprudence returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJRS jurisprudence rejected request with HTTP {response.status_code}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJRS jurisprudence response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJRS jurisprudence JSON root is not an object")
        return data, getattr(response, "url", url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


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
    return JurisprudenceResult(
        id=f"tjrs-solr-{external_id}",
        source="tjrs_solr",
        court=_first(item, "nome_tribunal", "origem") or "TJRS",
        type=_first(item, "tipo_documento", "tipo_processo") or "jurisprudencia",
        number=_first(item, "numero_processo"),
        summary=summary or None,
        rapporteur=_first(item, "nome_relator", "relator_redator") or None,
        updated_at=_first(item, "data_atualizacao") or None,
        judgment_date=_first(item, "data_julgamento") or None,
        publication_date=_first(item, "data_publicacao") or None,
        access_status=AccessStatus.PUBLIC,
        source_trace=trace,
        raw={
            **item,
            "orgao_julgador": _first(item, "orgao_julgador"),
            "document_url": document_url,
            "document_reference": document_reference or None,
        },
    )


def _first(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
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
