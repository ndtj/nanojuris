"""TST public jurisprudence REST provider."""

from __future__ import annotations

import hashlib
import re
import time
import unicodedata
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import build_canonical_document
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
    CanonicalDocument,
    DecisionBundle,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider

TST_ID_RE = re.compile(r"[a-f0-9]{32}", re.IGNORECASE)
CNJ_RE = re.compile(r"^(\d{7})[-.]?(\d{2})[-.]?(\d{4})[-.]?(\d)[-.]?(\d{2})[-.]?(\d{4})$")


class TstJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the public TST textual jurisprudence search."""

    name = "tst_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0
        self._last_http_metadata: dict[str, Any] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        payload = build_tst_search_payload(query)
        page_size = _page_size(query.page_size)
        endpoint = f"/rest/pesquisa-textual/{_page_start(query.page, page_size)}/{page_size}"
        data, source_url = self._request_json(endpoint, payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={
                "text": query.text,
                "number": query.number,
                "page": query.page,
                "page_size": page_size,
                "body_contract": "tst_pesquisa_textual_v1",
            },
            source_url=source_url,
            limitations=[
                "Consulta publica da jurisprudencia trabalhista do TST.",
                "A busca exige termo, numero ou filtro para evitar varredura acidental.",
                "O provider nao usa cookies pessoais, captcha ou bypass de controle.",
            ],
        )
        trace = _trace_with_http_metadata(trace, self._last_http_metadata)
        return parse_tst_search_response(data, query=query, trace=trace, api_url=self.api_url)

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document_id = _extract_document_id(precedent_id)
        endpoint = f"/rest/documentos/{document_id}"
        html, source_url = self._request_text(endpoint)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={"id": document_id},
            source_url=source_url,
            limitations=["Inteiro teor HTML publico retornado pelo backend oficial do TST."],
        )
        trace = _trace_with_http_metadata(trace, self._last_http_metadata)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": html, "content_type": "text/html"}],
            source_trace=trace,
            raw={"document_id": document_id, "document_url": source_url},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        external_id = _extract_document_id(document_id)
        endpoint = f"/rest/documentos/{external_id}"
        response = self._request("GET", endpoint)
        html = response.text
        source_url = getattr(response, "url", self.api_url + endpoint)
        content = bytes(getattr(response, "content", None) or html.encode("utf-8"))
        text = _clean_html(html)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={"id": external_id},
            source_url=source_url,
            limitations=["Documento publico retornado pela rota oficial de inteiro teor do TST."],
        )
        trace = _trace_with_http_metadata(trace, self._last_http_metadata)
        return build_canonical_document(
            document_id=f"tst-jurisprudencia-document-{external_id}",
            source=self.name,
            document_type="acordao",
            content=content,
            content_type=(getattr(response, "headers", None) or {}).get("Content-Type")
            or "text/html",
            title="TST inteiro teor",
            text_override=text,
            url=source_url,
            access_status=AccessStatus.PUBLIC,
            source_trace=trace,
            raw_metadata={"external_id": external_id},
            parser="tst_jurisprudencia.get_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TST Jurisprudencia",
            source_url=self.config.tst_jurisprudencia_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range", "filters"],
            document_types=["acordao", "decisao", "sumula", "precedente_normativo"],
            content_formats=["json", "html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "registry_id",
                "decision_type",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "disposition",
                "document_url",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /config.json",
                "POST /rest/pesquisa-textual/{inicio}/{limite}",
                "GET /rest/documentos/{id}",
                "GET /rest/orgaos-judicantes",
                "GET /rest/ministros",
                "GET /rest/convocados",
                "GET /rest/classes-processuais",
                "GET /rest/indicadores",
                "GET /rest/assuntos",
            ],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_live_tests=True,
            pagination_mode="offset",
            completeness_contract="reported_total_and_offset_window",
            supported_filters=[
                "text",
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "number",
                "published_from",
                "published_to",
                "updated_from",
                "updated_to",
                "types",
            ],
            limitations=[
                "A busca deve ter termo, numero ou filtro explicito.",
                "A base da API e publicada pelo config.json do frontend.",
                "O provider limita localmente page_size a 100 registros.",
            ],
            responsible_use=[
                "Usar consultas especificas e preservar SourceTrace.",
                "Tratar a fonte como jurisprudencia trabalhista do TST.",
                "Nao contornar bloqueios, captcha, login ou limites da fonte.",
            ],
        )

    @property
    def api_url(self) -> str:
        return self.config.tst_jurisprudencia_api_url.rstrip("/")

    def _request_json(self, endpoint: str, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
        response = self._request("POST", endpoint, json=payload)
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError(
                "TST jurisprudence API returned non-JSON content"
            ) from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TST jurisprudence API JSON root is not an object")
        return data, getattr(response, "url", self.api_url + endpoint)

    def _request_text(self, endpoint: str) -> tuple[str, str]:
        response = self._request("GET", endpoint)
        text = response.text
        if not text.strip():
            raise ParserContractChangedError("TST jurisprudence document response is empty")
        return text, getattr(response, "url", self.api_url + endpoint)

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> requests.Response:
        self._respect_rate_limit()
        url = urljoin(self.api_url + "/", endpoint.lstrip("/"))
        headers = {
            "Accept": "application/json, text/html, */*",
            "Content-Type": "application/json",
            "User-Agent": self.config.user_agent,
        }
        if method == "POST":
            headers["Referer"] = self.config.tst_jurisprudencia_url.rstrip("/") + "/"
        started = time.perf_counter()
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.config.timeout,
                allow_redirects=True,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TST jurisprudence request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TST jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TST jurisprudence requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TST jurisprudence returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TST jurisprudence rejected request with HTTP {response.status_code}"
            )
        if method == "POST" and response.text.lstrip().startswith("<"):
            raise ParserContractChangedError(
                "TST jurisprudence search returned HTML instead of JSON"
            )
        content = bytes(getattr(response, "content", None) or response.text.encode("utf-8"))
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": str(getattr(response, "url", None) or url),
            "content_type": (getattr(response, "headers", None) or {}).get("Content-Type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "retrieval_status": "ok" if 200 <= response.status_code < 300 else "http_error",
        }
        return response

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


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


def build_tst_search_payload(query: JurisprudenceQuery) -> dict[str, Any]:
    """Build the JSON body emitted by the official TST frontend."""

    if not any(
        [
            query.text,
            query.all_words,
            query.any_words,
            query.without_words,
            query.exact_phrase,
            query.number,
            query.published_from,
            query.published_to,
            query.updated_from,
            query.updated_to,
            query.types,
        ]
    ):
        raise ValueError("TST jurisprudence search requires a term, number or filter")
    return {
        "ou": query.any_words,
        "e": query.all_words or query.text,
        "termoExato": query.exact_phrase,
        "naoContem": query.without_words,
        "ementa": "",
        "dispositivo": "",
        "numeracaoUnica": _case_number_payload(query.number),
        "orgaosJudicantes": [],
        "ministros": [],
        "convocados": [],
        "classesProcessuais": [],
        "indicadores": [],
        "assuntos": [],
        "tipos": [_tst_type(value) for value in (query.types or ["ACORDAO"])],
        "orgao": "TST",
        "publicacaoInicial": query.published_from,
        "publicacaoFinal": query.published_to,
        "julgamentoInicial": query.updated_from,
        "julgamentoFinal": query.updated_to,
        "ordenacao": "numero" if query.order_by.strip().lower() in {"number", "numero"} else "data",
    }


def parse_tst_search_response(
    data: dict[str, Any],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    api_url: str,
) -> SearchPage:
    """Parse the TST REST search response into normalized results."""

    rows = data.get("registros")
    if not isinstance(rows, list):
        raise ParserContractChangedError("TST jurisprudence response missing registros list")
    results = [
        _record_to_result(row, trace=trace, api_url=api_url)
        for row in rows
        if isinstance(row, dict)
    ]
    page_size = _page_size(query.page_size)
    results = results[:page_size]
    total = _as_int(data.get("totalRegistros"), default=len(results))
    start = ((max(query.page, 1) - 1) * page_size) + 1 if results else 0
    complete, completeness_reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        total_is_authoritative="totalRegistros" in data,
    )
    return SearchPage(
        source="tst_jurisprudencia",
        total=total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=query.page,
        page_size=page_size,
        results=results,
        aggregations=_parse_aggregations(data.get("agregacoes")),
        source_trace=trace,
        pagination_mode="offset",
        is_complete=complete,
        completeness_reason=completeness_reason,
    )


def _record_to_result(
    row: dict[str, Any], *, trace: SourceTrace, api_url: str
) -> JurisprudenceResult:
    record = row.get("registro")
    if not isinstance(record, dict):
        raise ParserContractChangedError("TST jurisprudence row missing registro object")
    source_id = _optional_str(record.get("id"))
    if not source_id:
        raise ParserContractChangedError("TST jurisprudence record missing id")
    document_url = f"{api_url.rstrip('/')}/rest/documentos/{source_id}"
    source_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
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
    tipo_value = record.get("tipo")
    tipo: dict[str, Any] = tipo_value if isinstance(tipo_value, dict) else {}
    judging_body_value = record.get("orgaoJudicante")
    judging_body = (
        judging_body_value.get("descricao")
        if isinstance(judging_body_value, dict)
        else judging_body_value
    )
    court_value = record.get("orgao")
    court: dict[str, Any] = court_value if isinstance(court_value, dict) else {}
    summary = _usable_text(record.get("ementa")) or _clean_html(
        _optional_str(record.get("txtEmentaHighlight")) or ""
    )
    case_number = _optional_str(record.get("numFormatado")) or _format_case_number(
        record.get("numeracaoUnica")
    )
    return JurisprudenceResult(
        id=f"tst-jurisprudencia-{source_id}",
        source="tst_jurisprudencia",
        court=_optional_str(court.get("sigla")) or "TST",
        type=_map_type(tipo.get("nome") or record.get("codFase")),
        number=case_number,
        summary=summary or None,
        rapporteur=_optional_str(record.get("nomRelator")),
        updated_at=_optional_str(record.get("dtaPublicacao") or record.get("dtaJulgamento")),
        access_status=AccessStatus.PUBLIC if source_trace.http_status == 200 else None,
        source_trace=source_trace,
        raw={
            "registry_id": source_id,
            "case_class": _optional_str(record.get("codFase")),
            "orgao_julgador": _optional_str(judging_body),
            "court_name": _optional_str(court.get("nome")),
            "data_julgamento": _optional_str(record.get("dtaJulgamento")),
            "data_publicacao": _optional_str(record.get("dtaPublicacao")),
            "disposition": _usable_text(record.get("dispositivo")),
            "document_url": document_url,
            "full_text_url": document_url,
            "numeracao_unica": record.get("numeracaoUnica"),
            "source_record": record,
        },
    )


def _case_number_payload(value: str) -> dict[str, str]:
    match = CNJ_RE.match(value.strip()) if value else None
    if not match:
        return {"numero": value, "digito": "", "ano": "", "orgao": "5", "tribunal": "", "vara": ""}
    numero, digito, ano, orgao, tribunal, vara = match.groups()
    return {
        "numero": numero,
        "digito": digito,
        "ano": ano,
        "orgao": orgao,
        "tribunal": tribunal,
        "vara": vara,
    }


def _format_case_number(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    parts = [
        str(value.get(key) or "")
        for key in ("numero", "digito", "ano", "orgao", "tribunal", "vara")
    ]
    if not all(parts):
        return None
    return (
        f"{int(parts[0]):07d}-{int(parts[1]):02d}.{int(parts[2]):04d}."
        f"{int(parts[3]):01d}.{int(parts[4]):02d}.{int(parts[5]):04d}"
    )


def _extract_document_id(value: str) -> str:
    match = TST_ID_RE.search(value)
    if not match:
        raise ParserContractChangedError("TST document id is not a valid public registry id")
    return match.group(0)


def _map_type(value: Any) -> str:
    normalized = _without_accents(str(value or "").strip().lower())
    if "acordao" in normalized:
        return "acordao"
    if "sumula" in normalized:
        return "sumula"
    if "precedente" in normalized:
        return "precedente_normativo"
    if "despacho" in normalized or "decisao" in normalized:
        return "decisao"
    return normalized or "documento"


def _tst_type(value: str) -> str:
    normalized = _without_accents(str(value).strip().lower())
    mapping = {
        "acordao": "ACORDAO",
        "acordaos": "ACORDAO",
        "decisao": "DESPACHO",
        "despacho": "DESPACHO",
        "sumula": "SUM",
        "sumulas": "SUM",
        "precedente": "PN",
        "precedentes": "PN",
    }
    return mapping.get(normalized, str(value).upper())


def _parse_aggregations(value: Any) -> dict[str, list[dict[str, Any]]]:
    if isinstance(value, dict):
        return {
            str(key): [item for item in items if isinstance(item, dict)]
            for key, items in value.items()
            if isinstance(items, list)
        }
    if isinstance(value, list):
        return {"items": [item for item in value if isinstance(item, dict)]}
    return {}


def _clean_html(value: str) -> str:
    return " ".join(BeautifulSoup(value, "html.parser").get_text(" ", strip=True).split())


def _usable_text(value: Any) -> str | None:
    text = _clean_html(str(value)) if value is not None else ""
    return text if text and text.lower() != "removido no backend" else None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _page_size(value: int) -> int:
    return min(max(int(value or 1), 1), 100)


def _page_start(page: int, page_size: int) -> int:
    return (max(int(page or 1), 1) - 1) * page_size + 1


def _as_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _without_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char)
    )
