"""TJPB/PJe public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import time
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
        self._last_request = 0.0

    @property
    def base_url(self) -> str:
        return self.config.tjpb_pje_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
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
        source_url = getattr(response, "url", self.base_url + endpoint)
        soup = BeautifulSoup(html, "html.parser")
        for element in soup.select("script, style, noscript, nav, footer"):
            element.decompose()
        content = soup.select_one("main") or soup.select_one("#jurisprudencia") or soup.body
        text = _normalize_text(content.get_text("\n", strip=True) if content else "")
        if not text:
            raise ParserContractChangedError("TJPB detail returned empty public content")
        content_bytes = bytes(getattr(response, "content", None) or html.encode("utf-8"))
        headers = getattr(response, "headers", {}) or {}
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={"id": external_id},
            source_url=source_url,
            final_url=source_url,
            http_status=int(getattr(response, "status_code", 200) or 200),
            content_type=headers.get("Content-Type"),
            content_sha256=hashlib.sha256(content_bytes).hexdigest(),
            response_bytes=len(content_bytes),
        )
        return build_canonical_document(
            document_id=f"tjpb-pje-document-{external_id}",
            source=self.name,
            document_type="jurisprudencia",
            content=content_bytes,
            content_type=headers.get("Content-Type") or "text/html",
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
                "source_origin",
            ],
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
        return data, getattr(response, "url", self.base_url + endpoint)

    def _request_text(self, method: str, endpoint: str, **kwargs: Any) -> tuple[str, str]:
        response = self._request(method, endpoint, **kwargs)
        text = response.text
        if not text.strip():
            raise ParserContractChangedError("TJPB jurisprudence response is empty")
        return text, getattr(response, "url", self.base_url + endpoint)

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> requests.Response:
        self._respect_rate_limit()
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        try:
            response = self.session.request(
                method,
                url,
                headers={
                    "Accept": "application/json, text/html, */*",
                    "Content-Type": "application/json" if method == "POST" else "text/html",
                    "User-Agent": self.config.user_agent,
                },
                timeout=self.config.timeout,
                allow_redirects=True,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPB jurisprudence request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJPB jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJPB jurisprudence requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJPB jurisprudence returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJPB jurisprudence rejected request with HTTP {response.status_code}"
            )
        return response

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


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
    )


def _hit_to_result(
    item: dict[str, Any], *, trace: SourceTrace, base_url: str
) -> JurisprudenceResult:
    external_id = _optional_str(item.get("_id"))
    if not external_id:
        raise ParserContractChangedError("TJPB result missing _id")
    summary = _optional_str(item.get("ementa"))
    return JurisprudenceResult(
        id=f"tjpb-pje-{external_id}",
        source="tjpb_pje_jurisprudencia",
        court="TJPB",
        type="jurisprudencia_pje",
        number=_optional_str(item.get("numero_processo")),
        summary=summary,
        updated_at=_optional_str(item.get("dt_ementa")),
        source_trace=trace,
        raw={
            **item,
            "external_id": external_id,
            "document_url": urljoin(base_url + "/", f"jurisprudencia/view/{external_id}"),
            "full_text_url": urljoin(base_url + "/", f"jurisprudencia/view/{external_id}"),
        },
    )


def _build_search_object(query: JurisprudenceQuery) -> dict[str, Any]:
    types = {value.strip().lower() for value in query.types}
    return {
        "ementa": query.text or query.exact_phrase or "",
        "inteiro_teor": query.all_words or "",
        "nr_processo": query.number,
        "id_classe_judicial": query.types[0] if query.types else "",
        "id_orgao_julgador": query.source_origin,
        "id_relator": query.lawyer_name,
        "dt_inicio": query.published_from,
        "dt_fim": query.published_to,
        "id_origem": query.source_origin,
        "decisoes": bool(types & {"decisao", "decisão", "monocratica", "monocrática"}),
    }


def _public_query(query: JurisprudenceQuery) -> dict[str, Any]:
    return {
        "text": query.text,
        "number": query.number,
        "source_origin": query.source_origin,
        "published_from": query.published_from,
        "published_to": query.published_to,
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


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_int(value: object, *, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 10))
