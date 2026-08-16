"""TJCE SJURIS public jurisprudence provider."""

from __future__ import annotations

import base64
import hashlib
import json
import time
from datetime import date
from typing import Any
from urllib.parse import urljoin

import requests

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

SJURIS_PORTAL_URL = "https://sjuris.tjce.jus.br/"
SJURIS_DEFAULT_DOCUMENT_TYPES = ["ACÓRDÃO"]
SJURIS_DEFAULT_BASE = ["2º GRAU"]
SJURIS_DEFAULT_ORIGINS = ["PJE"]
SJURIS_MAX_PAGE_SIZE = 20


class TjceSjurisProvider(JurisprudenceProvider):
    """Provider for TJCE's public Angular SJURIS search gateway.

    The result contract was reproduced from the public browser application. The
    gateway returns the ementa, full text and an authenticated PDF payload in
    the search item itself. No independent detail route is assumed here.
    """

    name = "tjce_sjuris"

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
        return self.config.tjce_sjuris_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        remote_page = max(query.page - 1, 0)
        remote_size = _page_size(query.page_size)
        payload = build_tjce_sjuris_search_payload(query)
        endpoint = "/jurisprudencia/"
        data, source_url = self._request_json(
            endpoint,
            page=remote_page,
            size=remote_size,
            payload=payload,
        )
        trace = SourceTrace(
            provider=self.name,
            endpoint="POST /jurisprudencia/",
            query={
                "text": query.text,
                "page": query.page,
                "remote_page": remote_page,
                "requested_page_size": query.page_size,
                "effective_page_size": remote_size,
                "payload": payload,
            },
            source_url=source_url,
            limitations=[
                "O gateway foi observado com size 20; requests com size 50 e 100 "
                "retornaram HTTP 504.",
                "O texto integral e o PDF sao devolvidos inline no item; uma rota "
                "de detalhe independente ainda nao foi validada.",
                "O payload de datas e o filtro de relator ainda nao foram reproduzidos.",
            ],
            **self._last_http_metadata,
        )
        return parse_tjce_sjuris_response(data, query=query, trace=trace)

    def get_decisions(self, precedent_id: str):
        raise NotImplementedError(
            "TJCE/SJURIS entrega conteudo e PDF inline na busca; "
            "uma rota de detalhe independente ainda nao foi validada."
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJCE SJURIS",
            source_url=SJURIS_PORTAL_URL,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "pagination"],
            document_types=["acordao", "decisao_monocratica", "sumula"],
            content_formats=["json", "text", "pdf"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "full_text",
                "inline_pdf_base64",
                "pdf_content_sha256",
                "pdf_response_bytes",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "POST /jurisprudencia/?page={zero_based_page}&size={page_size}",
                "GET /jurisprudencia/buscaListaCampos/{field}",
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
            max_remote_page_size=SJURIS_MAX_PAGE_SIZE,
            completeness_contract="spring_page_total_elements",
            full_text_access="inline",
            supported_filters=[
                "text",
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "types",
                "source_origins",
            ],
            limitations=[
                "A interface observada usa ACÓRDÃO, 2º GRAU e PJE como filtros padrão.",
                "O gateway retornou HTTP 504 para size 50 e size 100 na validação live.",
                "Data de julgamento, relator e base documental ainda nao possuem payload "
                "reproduzido neste provider.",
                "O PDF e entregue em base64 no resultado; nao ha URL publica de detalhe "
                "confirmada.",
            ],
            responsible_use=[
                "Respeitar rate limit e manter page_size efetivo ate 20.",
                "Preservar o JSON bruto, o texto inline e o PDF base64 retornado pela fonte.",
                "Nao apresentar o PDF inline como documento carregado por uma rota independente.",
            ],
        )

    def _request_json(
        self,
        endpoint: str,
        *,
        page: int,
        size: int,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any], str]:
        self._respect_rate_limit()
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request_url = f"{url}?page={page}&size={size}"
        started = time.perf_counter()
        try:
            response = self.session.request(
                "POST",
                request_url,
                data=body,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Content-Type": "application/json",
                    "Origin": SJURIS_PORTAL_URL.rstrip("/"),
                    "Referer": SJURIS_PORTAL_URL,
                    "User-Agent": self.config.user_agent,
                },
                timeout=self.config.timeout,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJCE/SJURIS request failed: {exc}") from exc
        content = bytes(getattr(response, "content", b"") or response.text.encode("utf-8"))
        headers = getattr(response, "headers", {}) or {}
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": str(getattr(response, "url", request_url) or request_url),
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        if response.status_code == 429:
            raise RateLimitDetectedError("TJCE/SJURIS returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJCE/SJURIS requires access validation")
        if response.status_code in {400, 422}:
            raise QueryRejectedError(
                f"TJCE/SJURIS rejected the query with HTTP {response.status_code}"
            )
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJCE/SJURIS returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJCE/SJURIS rejected request with HTTP {response.status_code}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJCE/SJURIS response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJCE/SJURIS JSON root is not an object")
        return data, str(getattr(response, "url", request_url) or request_url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def build_tjce_sjuris_search_payload(query: JurisprudenceQuery) -> dict[str, Any]:
    """Build the browser payload reproduced from the public SJURIS UI."""

    return {
        "dataJulgamento": [],
        "busca": _build_search_expression(query),
        "ordenacao": _order_value(query.order_by),
        "nomeDocumento": _document_types(query.types),
        "baseDocumento": SJURIS_DEFAULT_BASE,
        "origem": list(query.source_origins) or SJURIS_DEFAULT_ORIGINS,
    }


def parse_tjce_sjuris_response(
    data: dict[str, Any],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
) -> SearchPage:
    """Parse the confirmed Spring-style SJURIS page envelope."""

    page_data = data.get("pagina")
    if not isinstance(page_data, dict) or not isinstance(page_data.get("content"), list):
        raise ParserContractChangedError("TJCE/SJURIS response missing pagina.content")
    items = page_data["content"]
    page_size = _page_size(query.page_size)
    results = [_item_to_result(item, trace=trace) for item in items if isinstance(item, dict)]
    reported_total = _as_int(page_data.get("totalElements"), default=len(results))
    start = ((max(query.page - 1, 0) * page_size) + 1) if results else 0
    complete, reason = page_completeness(
        reported_total=reported_total,
        start=start,
        returned=len(results),
        total_is_authoritative="totalElements" in page_data,
    )
    return SearchPage(
        source="tjce_sjuris",
        total=reported_total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=query.page,
        page_size=page_size,
        results=results,
        aggregations={
            "filtros": data.get("filtros", {}),
            "root_id": data.get("id"),
            "remote_page": page_data.get("number"),
            "remote_size": page_data.get("size"),
        },
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=reason,
    )


def _item_to_result(item: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    source_id = _first_value(item, "id", "idDocumento")
    if source_id is None:
        raise ParserContractChangedError("TJCE/SJURIS item missing stable id")
    full_text = _string_value(item.get("conteudo"))
    summary = _string_value(item.get("ementa"))
    pdf_value = _string_value(item.get("pdfAutenticadoBase64"))
    pdf_metadata: dict[str, Any] = {}
    if pdf_value:
        try:
            pdf_bytes = base64.b64decode(pdf_value, validate=True)
        except (ValueError, TypeError):
            pdf_bytes = b""
        if pdf_bytes:
            pdf_metadata = {
                "pdf_content_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
                "pdf_response_bytes": len(pdf_bytes),
            }
    judgment_date = _date_value(item.get("dataJulgamento"))
    publication_date = _date_value(item.get("dataPublicacao"))
    return JurisprudenceResult(
        id=f"tjce-sjuris-{source_id}",
        source="tjce_sjuris",
        court="TJCE",
        type=_decision_type(item.get("nomeDocumento")),
        number=_string_value(item.get("numeroProcesso")) or None,
        summary=summary or None,
        full_text=full_text or None,
        rapporteur=_string_value(item.get("magistrado")) or None,
        judgment_date=judgment_date,
        publication_date=publication_date,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(ExtractionStatus.COMPLETE if full_text else ExtractionStatus.PARTIAL),
        source_trace=trace,
        raw={
            **item,
            "case_class": _string_value(item.get("classe")) or None,
            "judging_body": _string_value(item.get("orgaoJulgador")) or None,
            "judgment_date": judgment_date,
            "publication_date": publication_date,
            "full_text_status": "inline" if full_text else "not_returned",
            "pdf_status": "inline_base64" if pdf_value else "not_returned",
            **pdf_metadata,
        },
    )


def _build_search_expression(query: JurisprudenceQuery) -> str:
    parts: list[str] = []
    if query.text.strip():
        parts.append(query.text.strip())
    if query.exact_phrase.strip():
        parts.append(f'"{query.exact_phrase.strip()}"')
    if query.all_words.strip():
        parts.append(" e ".join(query.all_words.split()))
    if query.any_words.strip():
        parts.append(" ou ".join(query.any_words.split()))
    if query.without_words.strip():
        parts.append("não " + " não ".join(query.without_words.split()))
    return " ".join(parts)


def _document_types(values: list[str]) -> list[str]:
    if not values:
        return list(SJURIS_DEFAULT_DOCUMENT_TYPES)
    known = {
        "acordao": "ACÓRDÃO",
        "acórdão": "ACÓRDÃO",
        "decisao_monocratica": "DECISÃO MONOCRÁTICA",
        "decisão monocrática": "DECISÃO MONOCRÁTICA",
        "sumula": "SÚMULA",
        "súmula": "SÚMULA",
    }
    return [known.get(value.strip().lower(), value.strip()) for value in values if value.strip()]


def _order_value(value: str) -> str:
    normalized = (value or "").strip().lower()
    return "order1" if normalized in {"", "text", "relevance", "relevancia"} else value


def _date_value(value: Any) -> str | None:
    if isinstance(value, list | tuple) and len(value) >= 3:
        try:
            return date(int(value[0]), int(value[1]), int(value[2])).isoformat()
        except (TypeError, ValueError):
            return None
    text = _string_value(value)
    if not text or text.lower() in {"n/d", "nd", "null"}:
        return None
    return text[:10]


def _decision_type(value: Any) -> str:
    text = _string_value(value).lower()
    return {
        "acórdão": "acordao",
        "decisão monocrática": "decisao_monocratica",
        "súmula": "sumula",
    }.get(text, text or "jurisprudencia")


def _first_value(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), SJURIS_MAX_PAGE_SIZE))
