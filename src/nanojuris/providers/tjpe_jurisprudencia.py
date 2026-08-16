"""TJPE public REST jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime
from html import unescape
from typing import Any
from urllib.parse import urljoin

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


class TjpeJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the public TJPE jurisprudence REST application."""

    name = "tjpe_jurisprudencia"

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
        return self.config.tjpe_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/api/v1/jurisprudencias"
        page_size = _page_size(query.page_size)
        params = build_tjpe_search_parameters(query, page_size=page_size)
        data, source_url = self._request_json(endpoint, params=params)
        trace_metadata = {
            key: value for key, value in self._last_http_metadata.items() if key != "reported_total"
        }
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /api/v1/jurisprudencias",
            query={"text": query.text, "page": query.page, "page_size": page_size, **params},
            source_url=source_url,
            limitations=[
                "A API usa pagina zero-based no transporte HTTP.",
                "Filtros por ids exigem catalogos oficiais de classes, assuntos ou unidades.",
                "Texto integral depende de textoAcordao ou textoDecisao presente no item.",
            ],
            **trace_metadata,
        )
        return parse_tjpe_search_response(
            data,
            query=query,
            trace=trace,
            reported_total=self._last_http_metadata.get("reported_total"),
        )

    def get_decisions(self, precedent_id: str):
        raise NotImplementedError(
            "TJPE expoe texto e metadados na busca; a rota auxiliar de processo nao e "
            "tratada como detalhe jurisprudencial neste provider."
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJPE Consulta de Jurisprudencia",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range", "pagination"],
            document_types=["acordao", "decisao"],
            content_formats=["json", "html"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "case_number",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "full_text",
                "source_key",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /api/v1/jurisprudencias",
                "GET /api/v1/classes",
                "GET /api/v1/assuntos",
                "GET /api/v1/relatores",
                "GET /api/v1/unidades-judiciais",
            ],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_live_tests=True,
            pagination_mode="offset",
            completeness_contract="x_total_count_and_page_window",
            full_text_access="inline",
            supported_filters=[
                "text",
                "number",
                "published_from",
                "published_to",
                "types",
                "order_by",
            ],
            limitations=[
                "A API pode retornar ementa nula e texto de decisao presente.",
                "A cadeia TLS do ambiente precisa ser valida; o provider nunca "
                "desativa verify_ssl.",
                "Filtros de catalogo por codigo ainda nao fazem parte da interface publica comum.",
            ],
            responsible_use=[
                "Respeitar rate limit e page_size moderado.",
                "Preservar SourceTrace e o JSON bruto de cada item.",
                "Nao confundir a rota auxiliar de processo com consulta processual geral.",
            ],
        )

    def _request_json(self, endpoint: str, **kwargs: Any) -> tuple[list[Any], str]:
        self._respect_rate_limit()
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        try:
            response = self.session.request(
                "GET",
                url,
                headers={"Accept": "application/json"},
                timeout=self.config.timeout,
                allow_redirects=True,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPE jurisprudence request failed: {exc}") from exc
        content = bytes(getattr(response, "content", b"") or response.text.encode("utf-8"))
        headers = getattr(response, "headers", {}) or {}
        total_header = headers.get("X-Total-Count") or headers.get("x-total-count")
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": getattr(response, "url", url),
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": "ok" if response.status_code < 400 else "error",
            "reported_total": _as_int(total_header),
        }
        if response.status_code == 429:
            raise RateLimitDetectedError("TJPE jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJPE jurisprudence requires access validation")
        if response.status_code in {400, 422}:
            raise QueryRejectedError(
                f"TJPE jurisprudence rejected the query with HTTP {response.status_code}"
            )
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJPE jurisprudence returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJPE jurisprudence rejected request with HTTP {response.status_code}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJPE jurisprudence response is not JSON") from exc
        if isinstance(data, list):
            return data, str(getattr(response, "url", url) or url)
        if isinstance(data, dict) and isinstance(data.get("content"), list):
            self._last_http_metadata["reported_total"] = _as_int(
                data.get("totalElements"), default=self._last_http_metadata.get("reported_total")
            )
            return data["content"], str(getattr(response, "url", url) or url)
        raise ParserContractChangedError("TJPE jurisprudence JSON root is not a result list")

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def build_tjpe_search_parameters(
    query: JurisprudenceQuery, *, page_size: int | None = None
) -> dict[str, Any]:
    """Build only parameters observed in the public TJPE application."""

    size = _page_size(page_size or query.page_size)
    params: dict[str, Any] = {"page": max(query.page - 1, 0), "size": size}
    if query.text:
        params["pesquisaLivre.contains"] = query.text
    if query.number:
        params["npuSemFormatacao.equals"] = re.sub(r"\D", "", query.number)
    if query.published_from:
        params["dataJulgamento.greaterThanOrEqual"] = _date_iso(query.published_from)
    if query.published_to:
        params["dataJulgamento.lessThanOrEqual"] = _date_iso(query.published_to)
    if query.types:
        params["tipoSentenca.in"] = query.types
    if query.order_by and query.order_by.lower() != "text":
        params["sort"] = f"dataJulgamento,{_sort_direction(query.order_by)}"
    return params


def parse_tjpe_search_response(
    data: list[Any],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    reported_total: int | None = None,
) -> SearchPage:
    """Parse the public TJPE result list without discarding source fields."""

    if not isinstance(data, list):
        raise ParserContractChangedError("TJPE jurisprudence result root must be a list")
    results = [
        _item_to_result(item, trace=trace)
        for item in data[: _page_size(query.page_size)]
        if isinstance(item, dict)
    ]
    total = reported_total if reported_total is not None else len(results)
    page_size = _page_size(query.page_size)
    start = (max(query.page - 1, 0) * page_size) + 1 if results else 0
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        total_is_authoritative=reported_total is not None,
    )
    return SearchPage(
        source="tjpe_jurisprudencia",
        total=total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=query.page,
        page_size=page_size,
        results=results,
        source_trace=trace,
        pagination_mode="offset",
        is_complete=complete,
        completeness_reason=reason,
    )


def _item_to_result(item: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    source_key = _first_string(item, "chave", "codigoProcesso", "npuSemFormatacao")
    if not source_key:
        raise ParserContractChangedError("TJPE jurisprudence item missing stable key")
    summary_raw = _first_string(item, "textoEmenta")
    full_text_raw = _first_string(item, "textoAcordao", "textoDecisao")
    summary = _html_to_text(summary_raw)
    full_text = _html_to_text(full_text_raw)
    judgment_raw = _first_string(item, "dataJulgamento", "dataJulgamentoString")
    publication_raw = _first_string(item, "dataPublicacao", "dataPublicacaoString")
    return JurisprudenceResult(
        id=f"tjpe-juris-{source_key}",
        source="tjpe_jurisprudencia",
        court="TJPE",
        type=_first_string(item, "tipoSentenca") or _infer_type(item),
        number=_first_string(item, "npu", "npuSemFormatacao", "numAntigo"),
        summary=summary or None,
        full_text=full_text or None,
        rapporteur=_first_string(item, "relator"),
        judgment_date=_date_iso(judgment_raw) if judgment_raw else None,
        publication_date=_date_iso(publication_raw) if publication_raw else None,
        updated_at=(
            _date_iso(publication_raw or judgment_raw)
            if (publication_raw or judgment_raw)
            else None
        ),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw={
            **item,
            "source_key": source_key,
            "summary_raw": summary_raw,
            "full_text_raw": full_text_raw,
            "judgment_date": _date_iso(judgment_raw) if judgment_raw else None,
            "publication_date": _date_iso(publication_raw) if publication_raw else None,
            "judging_body": _first_string(item, "nomeOrgaoJulgador", "codOrgaoJulgador"),
            "case_class": _first_string(item, "descrClasseCNJ", "classeCNJ"),
        },
    )


def _html_to_text(value: str) -> str:
    if not value:
        return ""
    text = BeautifulSoup(unescape(value), "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def _date_iso(value: str) -> str:
    text = value.strip()
    for pattern in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    for pattern in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    return text[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", text) else text


def _first_string(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _infer_type(item: dict[str, Any]) -> str:
    return "acordao" if item.get("textoAcordao") else "decisao"


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 100))


def _as_int(value: object, *, default: int | None = None) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _sort_direction(value: str) -> str:
    return "asc" if value.lower().endswith("asc") else "desc"
