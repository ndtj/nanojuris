"""TJMT public jurisprudence API provider."""

from __future__ import annotations

import hashlib
import html
import re
import time
from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

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
TJMT_DEFAULT_API_URL = "https://hellsgate.tjmt.jus.br/jurisprudencia"
TJMT_MAX_PAGE_SIZE = 100


class TjmtJurisprudenciaApiProvider(JurisprudenceProvider):
    """Provider for TJMT's public SPA-backed jurisprudence API.

    The SPA publishes its API base URL and application token in a public runtime
    configuration. Older deployments expose ``config.json``; the current SPA
    embeds the same values in a public JavaScript chunk. The token is read at
    runtime and is never placed in traces, fixtures, raw records or source
    configuration. It is an application value delivered to every public
    visitor, not a user credential.
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
        endpoint = "/consulta"
        data, source_url = self._request_json(
            runtime["api_url"], endpoint, params=params, token=runtime["token"]
        )
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
            data,
            query=query,
            trace=trace,
            api_type="Decisao" if params["tipoConsulta"] == "2" else "Acordao",
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
                "GET /jurisprudencia/consulta",
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
                "A fonte publica o api_url e o token de aplicacao no runtime da SPA; "
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
        except ValueError:
            return self._load_runtime_config_from_spa()
        if isinstance(data, dict):
            runtime = _runtime_config_from_mapping(data)
            if runtime is not None:
                return runtime
        return self._load_runtime_config_from_spa()

    def _load_runtime_config_from_spa(self) -> dict[str, str]:
        """Read the runtime values from the public SPA bundles.

        TJMT moved the public config from a JSON asset into an Angular bundle.
        We follow only same-origin script URLs published by the portal and
        reject arbitrary URLs, so this fallback remains a public-source read
        rather than an unrestricted URL fetch.
        """

        portal_url = self.base_url + "/"
        self._respect_rate_limit()
        try:
            response = self.session.request(
                "GET",
                portal_url,
                headers={"Accept": "text/html", "Referer": TJMT_PORTAL_URL},
                timeout=self.config.timeout,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJMT SPA request failed: {exc}") from exc
        _raise_runtime_http_error(response, "TJMT SPA")
        html_text = str(getattr(response, "text", "") or "")
        origin = urlsplit(str(getattr(response, "url", portal_url) or portal_url)).netloc
        queue = _same_origin_script_urls(html_text, portal_url, origin)
        seen: set[str] = set()
        inspected = 0
        while queue and inspected < 80:
            script_url = queue.pop(0)
            if script_url in seen:
                continue
            seen.add(script_url)
            inspected += 1
            self._respect_rate_limit()
            try:
                script_response = self.session.request(
                    "GET",
                    script_url,
                    headers={"Accept": "application/javascript", "Referer": portal_url},
                    timeout=self.config.timeout,
                    allow_redirects=True,
                )
            except requests.RequestException as exc:
                raise SourceUnavailableError(f"TJMT SPA script request failed: {exc}") from exc
            _raise_runtime_http_error(script_response, "TJMT SPA script")
            script_text = str(getattr(script_response, "text", "") or "")
            runtime = _runtime_config_from_script(script_text)
            if runtime is not None:
                return runtime
            for discovered in _same_origin_script_urls(script_text, script_url, origin):
                if discovered not in seen:
                    queue.append(discovered)
        raise ParserContractChangedError(
            "TJMT public SPA did not expose api_url and api_hellsgate_token"
        )

    def _request_json(
        self, api_url: str, endpoint: str, *, params: dict[str, Any], token: str
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
                    "token": token,
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
    """Build the query-string contract used by the current TJMT SPA.

    The current Angular bundle serializes the filter object directly.  In
    particular, it does not use the old ``filtro.*`` prefix and its page index
    is zero-based.
    """

    requested_type = query.types[0].strip().lower() if query.types else "acordao"
    tipo = "2" if "decis" in requested_type else "1"
    order = _order_value(query.order_by)
    return {
        "indicePagina": str(max(query.page - 1, 0)),
        "quantidadePagina": str(page_size or query.page_size),
        "tipoConsulta": tipo,
        "termoDeBusca": _search_term(query),
        "tipoBusca": "1",
        "OrdenarPor": "Relevancia" if order == "Relevancia" else "Julgamento",
        "Decrescente": str(order != "DataCrescente").lower(),
        "thesaurus": "false",
        "exibirArquivados": "true",
        "periodoDataDe": _date_iso(query.published_from),
        "periodoDataAte": _date_iso(query.published_to),
    }


def parse_tjmt_response(
    data: dict[str, Any], *, query: JurisprudenceQuery, trace: SourceTrace, api_type: str
) -> SearchPage:
    # Current deployments return {"value": {...}}, while the older public
    # deployment returned the inner object directly.
    payload = data.get("value") if isinstance(data.get("value"), dict) else data
    if not isinstance(payload, dict):
        raise ParserContractChangedError("TJMT response value is not an object")
    key = (
        "DecisaoMonocraticaCollection"
        if api_type.lower().startswith("decis")
        else "AcordaoCollection"
    )
    items = payload.get("resultados")
    if not isinstance(items, list):
        items = payload.get(key)
    if not isinstance(items, list):
        raise ParserContractChangedError(f"TJMT response missing resultados/{key}")
    effective_page_size = min(max(int(query.page_size or 10), 1), TJMT_MAX_PAGE_SIZE)
    results = [
        _item_to_result(item, trace=trace)
        for item in items[:effective_page_size]
        if isinstance(item, dict)
    ]
    total_key = "CountDecisaoMonocratica" if key.startswith("Decisao") else "CountAcordaoDocumento"
    reported_total = _as_int(
        payload.get(_current_total_key(total_key)),
        default=_as_int(payload.get("CountTotal", payload.get("countTotal")), default=len(results)),
    )
    page = max(query.page, 1)
    start = ((page - 1) * effective_page_size) + 1 if results else 0
    complete, reason = page_completeness(
        reported_total=reported_total,
        start=start,
        returned=len(results),
        total_is_authoritative=(
            total_key in payload
            or _current_total_key(total_key) in payload
            or "CountTotal" in payload
            or "countTotal" in payload
        ),
    )
    return SearchPage(
        source="tjmt_jurisprudencia_api",
        total=reported_total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=page,
        page_size=effective_page_size,
        results=results,
        aggregations={
            "count_total": payload.get("CountTotal", payload.get("countTotal")),
            "count_acordao": payload.get(
                "CountAcordaoDocumento", payload.get("countAcordaoDocumento")
            ),
            "count_decisao": payload.get(
                "CountDecisaoMonocratica", payload.get("countDecisaoMonocratica")
            ),
            "facets": {
                k: value
                for k, value in payload.items()
                if k.startswith("Facet") or k.startswith("facet")
            },
        },
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=reason,
    )


def _item_to_result(item: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    process = _first_value(item, "Processo", "processo")
    if not isinstance(process, dict):
        process = {}
    source_id = _first_value(item, "Id", "id") or _first_value(process, "UID", "uid")
    if source_id is None:
        raise ParserContractChangedError("TJMT item missing stable Id")
    document_html = _string_value(
        _first_value(item, "Documento", "documento", "documentoHtml", "documentHtml")
    )
    full_text = _html_text(document_html)
    summary = _html_text(_string_value(_first_value(item, "Conteudo", "conteudo"))) or None
    judgment_date = _date_value(_first_value(process, "DataJulgamento", "dataJulgamento"))
    publication_date = _date_value(_first_value(process, "DataPublicacao", "dataPublicacao"))
    return JurisprudenceResult(
        id=f"tjmt-jurisprudencia-{source_id}",
        source="tjmt_jurisprudencia_api",
        court="TJMT",
        type=_decision_type(_first_value(item, "Tipo", "tipo")),
        number=_string_value(_first_value(process, "NumeroUnicoFormatado", "numeroUnicoFormatado"))
        or None,
        summary=summary,
        full_text=full_text or None,
        status=_string_value(_first_value(process, "Julgamento", "julgamento")) or None,
        rapporteur=_string_value(_first_value(process, "NomeRelator", "nomeRelator")) or None,
        judgment_date=judgment_date,
        publication_date=publication_date,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(ExtractionStatus.COMPLETE if full_text else ExtractionStatus.PARTIAL),
        source_trace=trace,
        raw={
            **item,
            "case_class": _string_value(
                _first_value(process, "NomeClasseEsferaProcessual", "nomeClasseEsferaProcessual")
            )
            or None,
            "subject": _string_value(_first_value(process, "Assunto", "assunto")) or None,
            "judging_body": _string_value(
                _first_value(process, "DescricaoCamara", "descricaoCamara")
            )
            or None,
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


def _date_iso(value: str) -> str:
    if not value:
        return ""
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, pattern).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value


def _order_value(value: str) -> str:
    return (
        "DataDecrescente"
        if (value or "").strip().lower() in {"", "text", "date", "recent"}
        else value
    )


def _current_total_key(legacy_key: str) -> str:
    return {
        "CountAcordaoDocumento": "countAcordaoDocumento",
        "CountDecisaoMonocratica": "countDecisaoMonocratica",
    }.get(legacy_key, legacy_key)


def _first_value(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


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


def _runtime_config_from_mapping(data: dict[str, Any]) -> dict[str, str] | None:
    api_url = str(data.get("api_url") or "").strip().rstrip("/")
    token = str(data.get("api_hellsgate_token") or "").strip()
    if not api_url or not token:
        return None
    if not api_url.startswith("https://"):
        raise ParserContractChangedError("TJMT config api_url is not HTTPS")
    return {"api_url": api_url, "token": token}


def _runtime_config_from_script(script: str) -> dict[str, str] | None:
    api_url_match = re.search(r"\bapi_url\s*:\s*['\"](https://[^'\"]+)['\"]", script)
    token_match = re.search(r"\bapi_hellsgate_token\s*:\s*['\"]([^'\"]+)['\"]", script)
    if not api_url_match or not token_match:
        return None
    return {"api_url": api_url_match.group(1).rstrip("/"), "token": token_match.group(1)}


def _same_origin_script_urls(text: str, base_url: str, origin: str) -> list[str]:
    candidates = re.findall(
        r"(?:src\s*=\s*|import\(\s*|['\"])([^'\"\s<>]+?\.js(?:\?[^'\"\s<>]*)?)",
        text,
        flags=re.IGNORECASE,
    )
    urls: list[str] = []
    for candidate in candidates:
        url = urljoin(base_url, candidate)
        parsed = urlsplit(url)
        if parsed.scheme == "https" and parsed.netloc == origin and url not in urls:
            urls.append(url)
    return urls


def _raise_runtime_http_error(response: Any, label: str) -> None:
    status = int(getattr(response, "status_code", 0) or 0)
    if status == 429:
        raise RateLimitDetectedError(f"{label} returned HTTP 429")
    if status in {401, 403}:
        raise AccessControlRequiredError(f"{label} requires access validation")
    if status >= 500:
        raise SourceUnavailableError(f"{label} returned HTTP {status}")
    if status >= 400:
        raise SourceUnavailableError(f"{label} returned HTTP {status}")
