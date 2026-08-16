"""TJMT public jurisprudence API provider."""

from __future__ import annotations

import hashlib
import html
import time
from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

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
    ExtractionStatus,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider

TJMT_PORTAL_URL = "https://jurisprudencia.tjmt.jus.br/"
TJMT_CONFIG_PATH = "/assets/config/config.json"
TJMT_DEFAULT_API_URL = "https://hellsgate-preview.tjmt.jus.br/jurisprudencia"
TJMT_MAX_PAGE_SIZE = 100


class TjmtJurisprudenciaApiProvider(JurisprudenceProvider):
    """Provider for TJMT's public SPA-backed jurisprudence API.

    The SPA publishes its API base URL and application token in ``config.json``.
    The token is read at runtime and is never placed in traces, fixtures, raw
    records or source configuration. It is an application value delivered to
    every public visitor, not a user credential.
    """

    name = "tjmt_jurisprudencia_api"

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
        return self.config.tjmt_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        runtime = self._load_runtime_config()
        page_size = min(max(int(query.page_size or 10), 1), TJMT_MAX_PAGE_SIZE)
        params = build_tjmt_search_params(query, page_size=page_size)
        params["token"] = runtime["token"]
        endpoint = f"/api/consulta/{params.pop('filtro.tipoConsulta')}"
        data, source_url = self._request_json(runtime["api_url"], endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"GET {endpoint}",
            query={
                "text": query.text,
                "page": query.page,
                "page_size": page_size,
                "requested_page_size": query.page_size,
                "filters": {
                    "published_from": query.published_from,
                    "published_to": query.published_to,
                    "types": query.types,
                },
            },
            source_url=source_url,
            limitations=[
                "O token de aplicacao e lido do config.json publico em cada busca "
                "e nao e persistido pelo provider.",
                "O campo Documento HTML e entregue inline na resposta de busca; "
                "a rota de relatorio independente foi observada, mas nao validada "
                "como carregamento estavel nesta rodada.",
                "Filtros de relator, orgao julgador e booleanos avancados ainda "
                "nao foram reproduzidos como contrato do provider.",
            ],
            **self._last_http_metadata,
        )
        return parse_tjmt_response(
            data, query=query, trace=trace, api_type=endpoint.rsplit("/", 1)[-1]
        )

    def get_decisions(self, precedent_id: str):
        raise NotImplementedError(
            "TJMT entrega o Documento HTML inline na busca; a rota de relatorio "
            "independente ainda nao possui contrato reproduzido neste provider."
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJMT Jurisprudencia API",
            source_url=TJMT_PORTAL_URL,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "pagination"],
            document_types=["acordao", "decisao_monocratica"],
            content_formats=["json", "html", "text"],
            canonical_records=["CanonicalDecision"],
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
                "document_html",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /assets/config/config.json",
                "GET /jurisprudencia/api/consulta/{tipoConsulta}",
                "GET /jurisprudencia/VisualizaRelatorio/RetornaDocumentoAcordao",
            ],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_live_tests=True,
            pagination_mode="page",
            max_remote_page=None,
            max_remote_page_size=TJMT_MAX_PAGE_SIZE,
            completeness_contract="CountAcordaoDocumento_or_CountDecisaoMonocratica",
            full_text_access="inline",
            supported_filters=[
                "text",
                "published_from",
                "published_to",
                "types",
                "order_by",
            ],
            limitations=[
                "A fonte publica o api_url e o token de aplicacao em config.json; "
                "o valor nao e armazenado pelo provider.",
                "O inteiro teor textual e extraido do campo Documento HTML inline.",
                "A rota de relatorio independente ainda nao foi validada com contrato estavel.",
            ],
            responsible_use=[
                "Respeitar timeout e rate_limit_interval.",
                "Preservar o item JSON e o Documento HTML em raw.",
                "Nao tratar erro de autenticacao da API como resultado vazio.",
            ],
        )

    def _load_runtime_config(self) -> dict[str, str]:
        self._respect_rate_limit()
        url = self.base_url + TJMT_CONFIG_PATH
        try:
            response = self.session.request(
                "GET",
                url,
                headers={"Accept": "application/json", "Referer": TJMT_PORTAL_URL},
                timeout=self.config.timeout,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJMT config request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJMT config returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJMT config requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJMT config returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"TJMT config returned HTTP {response.status_code}")
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJMT config is not JSON") from exc
        api_url = str(data.get("api_url") or "").strip().rstrip("/")
        token = str(data.get("api_hellsgate_token") or "").strip()
        if not api_url or not token:
            raise ParserContractChangedError("TJMT config missing api_url or api_hellsgate_token")
        if not api_url.startswith("https://"):
            raise ParserContractChangedError("TJMT config api_url is not HTTPS")
        return {"api_url": api_url, "token": token}

    def _request_json(
        self, api_url: str, endpoint: str, *, params: dict[str, Any]
    ) -> tuple[dict[str, Any], str]:
        self._respect_rate_limit()
        url = api_url.rstrip("/") + endpoint
        started = time.perf_counter()
        try:
            response = self.session.request(
                "GET",
                url,
                params=params,
                headers={
                    "Accept": "application/json",
                    "Origin": TJMT_PORTAL_URL.rstrip("/"),
                    "Referer": TJMT_PORTAL_URL,
                },
                timeout=self.config.timeout,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJMT jurisprudence request failed: {exc}") from exc
        content = bytes(getattr(response, "content", b"") or response.text.encode("utf-8"))
        headers = getattr(response, "headers", {}) or {}
        safe_url = _without_token(str(getattr(response, "url", url) or url))
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": safe_url,
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        if response.status_code == 429:
            raise RateLimitDetectedError("TJMT jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJMT jurisprudence requires access validation")
        if response.status_code in {400, 422}:
            raise QueryRejectedError(
                f"TJMT jurisprudence rejected the query with HTTP {response.status_code}"
            )
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJMT jurisprudence returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"TJMT jurisprudence returned HTTP {response.status_code}")
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJMT jurisprudence response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJMT jurisprudence JSON root is not an object")
        return data, safe_url

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def build_tjmt_search_params(
    query: JurisprudenceQuery, *, page_size: int | None = None
) -> dict[str, Any]:
    """Build the public query-string contract used by the TJMT SPA."""

    requested_type = query.types[0].strip().lower() if query.types else "acordao"
    tipo = "Decisao" if "decis" in requested_type else "Acordao"
    return {
        "filtro.isBasica": "false",
        "filtro.indicePagina": str(query.page),
        "filtro.quantidadePagina": str(page_size or query.page_size),
        "filtro.tipoConsulta": tipo,
        "filtro.termoDeBusca": _search_term(query),
        "filtro.periodoDataDe": _date_br(query.published_from),
        "filtro.periodoDataAte": _date_br(query.published_to),
        "filtro.tipoBusca": "1",
        "filtro.relator": "",
        "filtro.julgamento": "",
        "filtro.orgaoJulgador": "",
        "filtro.colegiado": "",
        "filtro.ordenacao.ordenarPor": _order_value(query.order_by),
        "filtro.ordenacao.ordenarDataPor": "Julgamento",
        "filtro.thesaurus": "false",
    }


def parse_tjmt_response(
    data: dict[str, Any], *, query: JurisprudenceQuery, trace: SourceTrace, api_type: str
) -> SearchPage:
    key = (
        "DecisaoMonocraticaCollection"
        if api_type.lower().startswith("decis")
        else "AcordaoCollection"
    )
    items = data.get(key)
    if not isinstance(items, list):
        raise ParserContractChangedError(f"TJMT response missing {key}")
    results = [_item_to_result(item, trace=trace) for item in items if isinstance(item, dict)]
    total_key = "CountDecisaoMonocratica" if key.startswith("Decisao") else "CountAcordaoDocumento"
    reported_total = _as_int(
        data.get(total_key), default=_as_int(data.get("CountTotal"), default=len(results))
    )
    start = ((query.page - 1) * query.page_size) + 1 if results else 0
    complete, reason = page_completeness(
        reported_total=reported_total,
        start=start,
        returned=len(results),
        total_is_authoritative=total_key in data or "CountTotal" in data,
    )
    return SearchPage(
        source="tjmt_jurisprudencia_api",
        total=reported_total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=query.page,
        page_size=min(max(query.page_size, 1), TJMT_MAX_PAGE_SIZE),
        results=results,
        aggregations={
            "count_total": data.get("CountTotal"),
            "count_acordao": data.get("CountAcordaoDocumento"),
            "count_decisao": data.get("CountDecisaoMonocratica"),
            "facets": {k: data.get(k) for k in data if k.startswith("Facet")},
        },
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=reason,
    )


def _item_to_result(item: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    process = item.get("Processo")
    if not isinstance(process, dict):
        process = {}
    source_id = item.get("Id") or process.get("UID")
    if source_id is None:
        raise ParserContractChangedError("TJMT item missing stable Id")
    document_html = _string_value(item.get("Documento"))
    full_text = _html_text(document_html)
    summary = _html_text(_string_value(item.get("Conteudo"))) or None
    judgment_date = _date_value(process.get("DataJulgamento"))
    publication_date = _date_value(process.get("DataPublicacao"))
    return JurisprudenceResult(
        id=f"tjmt-jurisprudencia-{source_id}",
        source="tjmt_jurisprudencia_api",
        court="TJMT",
        type=_decision_type(item.get("Tipo")),
        number=_string_value(process.get("NumeroUnicoFormatado")) or None,
        summary=summary,
        full_text=full_text or None,
        status=_string_value(process.get("Julgamento")) or None,
        rapporteur=_string_value(process.get("NomeRelator")) or None,
        judgment_date=judgment_date,
        publication_date=publication_date,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(ExtractionStatus.COMPLETE if full_text else ExtractionStatus.PARTIAL),
        source_trace=trace,
        raw={
            **item,
            "case_class": _string_value(process.get("NomeClasseEsferaProcessual")) or None,
            "subject": _string_value(process.get("Assunto")) or None,
            "judging_body": _string_value(process.get("DescricaoCamara")) or None,
            "judgment_date": judgment_date,
            "publication_date": publication_date,
            "document_html": document_html or None,
            "document_content_type": "text/html" if document_html else None,
            "full_text_status": "inline" if full_text else "not_returned",
        },
    )


def _html_text(value: str) -> str:
    if not value:
        return ""
    text = BeautifulSoup(html.unescape(value), "html.parser").get_text(" ", strip=True)
    return " ".join(text.split())


def _search_term(query: JurisprudenceQuery) -> str:
    parts = [query.text.strip()] if query.text.strip() else []
    if query.exact_phrase.strip():
        parts.append(f'"{query.exact_phrase.strip()}"')
    return " ".join(parts)


def _date_br(value: str) -> str:
    if not value:
        return ""
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, pattern).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return value


def _order_value(value: str) -> str:
    return (
        "DataDecrescente"
        if (value or "").strip().lower() in {"", "text", "date", "recent"}
        else value
    )


def _date_value(value: Any) -> str | None:
    text = _string_value(value)
    if not text or text.lower() in {"n/d", "nd", "null"}:
        return None
    return text[:10]


def _decision_type(value: Any) -> str:
    text = _string_value(value).lower()
    return {"acordao": "acordao", "decisao": "decisao_monocratica"}.get(
        text, text or "jurisprudencia"
    )


def _string_value(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _as_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _without_token(value: str) -> str:
    parts = urlsplit(value)
    query = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() != "token"
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
