"""TRF5 public HTML jurisprudence provider."""

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
from nanojuris.providers.base import JurisprudenceProvider

SEARCH_PATH = "/jurisprudencia/pesquisa.wsp"
RESULT_PATH = "/jurisprudencia/resultado_pesquisa.wsp"
DETAIL_PATH = "/jurisprudencia/exibe_modelo.wsp"
PROCESS_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
DOCUMENT_ID_RE = re.compile(r"detalhesDocumento\(['\"](\d+)['\"]\)")
TOKEN_RE = re.compile(r'name=["\']wi\.token["\'][^>]*value=["\']([^"\']+)')


class Trf5JurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the public TRF5 jurisprudence search."""

    name = "trf5_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0
        self._last_response_content = b""
        self._last_response_content_type: str | None = None
        self._last_http_metadata: dict[str, Any] = {}

    @property
    def base_url(self) -> str:
        return self.config.trf5_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        if query.page != 1:
            raise UnsupportedQueryError(
                "TRF5 ainda nao possui paginacao remota comprovada; use page=1."
            )
        term = (query.text or query.exact_phrase or query.number).strip()
        if not term:
            raise ValueError("TRF5 jurisprudence search requires a term or number")
        initial_html, initial_url = self._request_text("GET", SEARCH_PATH)
        payload = _build_search_payload(query)
        token = _extract_token(initial_html)
        if token:
            payload["wi.token"] = token
        html, source_url = self._request_text("POST", RESULT_PATH, data=payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=RESULT_PATH,
            query={**payload, "wi.token": "<session-token>"} if token else payload,
            source_url=source_url or initial_url,
            limitations=[
                "O token wi.token e obtido da sessao corrente e nao e persistido.",
                "A resposta HTML pode alterar labels e codificacao sem aviso.",
                "Paginacao e ordenacao ainda nao foram promovidas para coleta em escala.",
            ],
            **self._last_http_metadata,
        )
        results = parse_trf5_results(html, trace=trace, base_url=self.base_url)
        page_size = _page_size(query.page_size)
        limited = results[:page_size]
        start = ((max(query.page, 1) - 1) * page_size) + 1 if limited else 0
        return SearchPage(
            source=self.name,
            total=len(results),
            start=start,
            end=start + len(limited) - 1 if limited else 0,
            page=max(query.page, 1),
            page_size=page_size,
            results=limited,
            source_trace=trace,
            pagination_mode="unknown",
            is_complete=False,
            completeness_reason=(
                "A resposta HTML observada representa a primeira pagina; o contrato "
                "de paginação remota ainda não foi promovido."
            ),
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document_id = _extract_document_id(precedent_id)
        html, source_url = self._request_text(
            "GET", DETAIL_PATH, params={"tmp.anexo.id_documento": document_id}
        )
        trace = SourceTrace(
            provider=self.name,
            endpoint=DETAIL_PATH,
            query={"tmp.anexo.id_documento": document_id},
            source_url=source_url,
            limitations=["Inteiro teor HTML publico retornado pela fonte TRF5."],
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": html, "content_type": "text/html"}],
            source_trace=trace,
            raw={"id_documento": document_id},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        bundle = self.get_decisions(document_id)
        content = str(bundle.texts[0]["content"])
        raw_content = self._last_response_content or content.encode("utf-8")
        return build_canonical_document(
            document_id=f"trf5-jurisprudencia-document-{_extract_document_id(document_id)}",
            source=self.name,
            document_type="jurisprudencia",
            content=raw_content,
            content_type=self._last_response_content_type or "text/html",
            title="TRF5 Jurisprudencia",
            text_override=content,
            url=bundle.source_trace.source_url if bundle.source_trace else None,
            access_status=AccessStatus.PUBLIC,
            source_trace=bundle.source_trace,
            raw_metadata=bundle.raw,
            parser="trf5_jurisprudencia.get_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TRF5 Jurisprudencia",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range"],
            document_types=["acordao", "decisao_monocratica", "informativo", "sumula"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "judging_body",
                "judgment_date",
                "summary",
                "document_url",
                "id_documento",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /jurisprudencia/pesquisa.wsp",
                "POST /jurisprudencia/resultado_pesquisa.wsp",
                "GET /jurisprudencia/exibe_modelo.wsp?tmp.anexo.id_documento=<id>",
            ],
            supports_full_text=True,
            pagination_mode="none",
            completeness_contract="observed_window_only",
            full_text_access="detail_call",
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_live_tests=True,
            supported_filters=["text", "number", "published_from", "published_to", "types"],
            limitations=[
                "O parser trabalha com a pagina retornada pela fonte e ainda nao promove "
                "paginacao.",
                "O token de sessao e dinamico e nunca deve ser salvo em fixture.",
                "A fonte usa HTML legado e ISO-8859-1 em respostas observadas.",
            ],
            responsible_use=[
                "Usar page_size pequeno e intervalo entre chamadas.",
                "Preservar o id_documento e SourceTrace para auditoria.",
                "Nao contornar bloqueios, tokens expirados ou controles da fonte.",
            ],
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> tuple[str, str]:
        self._respect_rate_limit()
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        try:
            response = self.session.request(
                method,
                url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "User-Agent": self.config.user_agent,
                },
                timeout=self.config.timeout,
                allow_redirects=True,
                verify=self.config.verify_ssl,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TRF5 jurisprudence request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TRF5 jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TRF5 jurisprudence requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TRF5 jurisprudence returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"TRF5 jurisprudence rejected HTTP {response.status_code}")
        response.encoding = response.encoding or "iso-8859-1"
        self._last_response_content = bytes(
            getattr(response, "content", None) or response.text.encode("utf-8")
        )
        self._last_response_content_type = (getattr(response, "headers", None) or {}).get(
            "Content-Type"
        )
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": getattr(response, "url", url),
            "content_type": self._last_response_content_type,
            "content_sha256": hashlib.sha256(self._last_response_content).hexdigest(),
            "response_bytes": len(self._last_response_content),
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        text = response.text
        if "captcha" in text.lower() or "acesso negado" in text.lower():
            raise AccessControlRequiredError("TRF5 jurisprudence returned access-control HTML")
        return text, getattr(response, "url", url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def parse_trf5_results(
    html: str, *, trace: SourceTrace, base_url: str
) -> list[JurisprudenceResult]:
    """Parse result rows from the public TRF5 HTML response."""

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("td.grid")
    if not rows:
        text = soup.get_text(" ", strip=True).lower()
        if "nenhum" in text or "no resultado" in text:
            return []
        raise ParserContractChangedError("TRF5 result rows not found")
    results: list[JurisprudenceResult] = []
    for row in rows:
        text = _clean_text(row.get_text(" ", strip=True))
        number_match = PROCESS_RE.search(text)
        if not number_match:
            continue
        document_match = DOCUMENT_ID_RE.search(str(row))
        if not document_match:
            raise ParserContractChangedError("TRF5 result row missing document id")
        document_id = document_match.group(1)
        metadata = _parse_metadata(text)
        summary = _extract_summary(text)
        results.append(
            JurisprudenceResult(
                id=f"trf5-jurisprudencia-{document_id}",
                source="trf5_jurisprudencia",
                court="TRF5",
                type=_normalize_type(metadata.get("tipo_documento")),
                number=number_match.group(0),
                summary=summary,
                updated_at=metadata.get("data_julgamento"),
                judgment_date=metadata.get("data_julgamento"),
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.COMPLETE,
                source_trace=trace,
                raw={
                    **metadata,
                    "id_documento": document_id,
                    "document_url": urljoin(
                        base_url + "/",
                        f"jurisprudencia/exibe_modelo.wsp?tmp.anexo.id_documento={document_id}",
                    ),
                },
            )
        )
    if not results:
        raise ParserContractChangedError("TRF5 result rows did not contain jurisprudence records")
    return results


def _build_search_payload(query: JurisprudenceQuery) -> dict[str, str]:
    return {
        "tmp.search.query": query.text or query.exact_phrase or query.number,
        "tmp.search.query_complemento": "",
        "tmp.ds_legislacao_2": "",
        "tmp.search.qtdade_registros": str(_page_size(query.page_size)),
        "tmp.search.acao": "novapesquisa",
    }


def _parse_metadata(text: str) -> dict[str, str]:
    patterns = {
        "orgao_julgador": r"(?:Órgão|Orgao) Julgador:\s*(.*?)\s*/\s*Tipo de Documento:",
        "tipo_documento": r"Tipo de Documento:\s*(.*?)\s*/\s*Data de Julgamento:",
        "data_julgamento": r"Data de Julgamento:\s*(.*?)\s*/\s*Nr\. Processo:",
    }
    values: dict[str, str] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.I)
        if match:
            values[key] = _clean_text(match.group(1))
    return values


def _extract_summary(text: str) -> str | None:
    match = re.search(r"EMENTA:\s*(.+)$", text, re.I)
    return _clean_text(match.group(1)) if match else None


def _extract_token(html: str) -> str | None:
    match = TOKEN_RE.search(html)
    return match.group(1) if match else None


def _extract_document_id(value: str) -> str:
    match = re.search(r"(\d+)$", value.strip())
    if not match:
        raise ParserContractChangedError("TRF5 jurisprudence id must end with digits")
    return match.group(1)


def _normalize_type(value: str | None) -> str:
    normalized = _clean_text(value or "").lower()
    return {
        "acórdãos": "acordao",
        "acordaos": "acordao",
        "decisões monocráticas": "decisao_monocratica",
        "decisoes monocraticas": "decisao_monocratica",
    }.get(normalized, normalized or "jurisprudencia")


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 50))
