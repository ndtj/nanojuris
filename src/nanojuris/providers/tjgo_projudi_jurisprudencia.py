"""TJGO/Projudi public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import time
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from nanojuris.config import NanoJurisConfig, configure_requests_session
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
    ExtractionStatus,
    ExtractionTrace,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider

CNJ_PATTERN = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
FILE_ID_PATTERN = re.compile(r"abrirArquivo\(\s*'[^']+'\s*,\s*'(?P<id>\d+)'\s*\)")


class TjgoProjudiJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for public TJGO/Projudi jurisprudence search results."""

    name = "tjgo_projudi_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/ConsultaJurisprudencia"
        payload = _build_payload(query)
        html = self._request_text("POST", endpoint, data=payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=payload,
            source_url=urljoin(
                self.config.tjgo_projudi_url.rstrip("/") + "/", endpoint.lstrip("/")
            ),
            limitations=[
                "Fonte HTML publica do PROJUDI/TJGO sujeita a mudancas de layout.",
                "O provider preserva o texto publico retornado pela fonte, "
                "sem redaction automatica.",
                "Download separado por Id_Arquivo permanece pendente ate contrato publico limpo.",
            ],
        )
        return parse_tjgo_results(
            html,
            query=query,
            trace=trace,
            base_url=self.config.tjgo_projudi_url,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise NotImplementedError(
            "TJGO/Projudi nao possui rota de detalhe estavel no provider atual; "
            "use get_document com um resultado que contenha texto embutido."
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        raise NotImplementedError(
            "TJGO/Projudi retorna inteiro teor embutido nos resultados de busca; "
            "baixa por Id_Arquivo ainda nao foi promovida por contrato publico limpo."
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJGO PROJUDI Jurisprudencia",
            source_url=self.config.tjgo_projudi_url,
            category="court_jurisprudence",
            search_modes=[
                "full_text",
                "case_number",
                "date_range",
                "decision_type",
                "judge",
                "unit",
            ],
            document_types=["decisao", "sentenca", "acordao"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "rapporteur",
                "judging_body",
                "publication_date",
                "summary",
                "full_text",
                "file_id",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /ConsultaJurisprudencia",
                "POST /ConsultaJurisprudencia",
            ],
            supports_full_text=False,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            pagination_mode="page",
            completeness_contract="reported_total_and_page_window",
            supported_filters=["text", "number"],
            limitations=[
                "O inteiro teor pode ser extraido do HTML de resultado quando a fonte "
                "o embute no card; "
                "isso nao equivale a get_document por id.",
                "A rota de download por Id_Arquivo voltou ao formulario em probe "
                "sem token e nao e usada.",
                "O HTML contem mencoes globais a captcha em assets, mas resultados "
                "juridicos validos prevalecem.",
            ],
            responsible_use=[
                "Usar coletas paginadas com rate limit.",
                "Nao tentar resolver captcha, token ou area autenticada.",
                "Preservar SourceTrace e raw metadata para auditoria profissional.",
            ],
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        self._respect_rate_limit()
        url = urljoin(self.config.tjgo_projudi_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.config.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJGO/Projudi request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJGO/Projudi returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJGO/Projudi returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJGO/Projudi rejected request with HTTP {response.status_code}"
            )
        text = _decode_response_text(response)
        if _looks_like_blocked_page(text):
            raise AccessControlRequiredError("TJGO/Projudi returned access-control HTML")
        return text

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def parse_tjgo_results(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    """Parse TJGO/Projudi result HTML into normalized records."""

    if _looks_like_blocked_page(html):
        raise AccessControlRequiredError("TJGO/Projudi returned access-control HTML")
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.search-result")
    total = _parse_total(soup)
    if not cards:
        complete, completeness_reason = page_completeness(
            reported_total=total,
            start=0,
            returned=0,
            total_is_authoritative=total > 0,
        )
        return SearchPage(
            source="tjgo_projudi_jurisprudencia",
            total=total,
            start=0,
            end=0,
            page=query.page,
            page_size=query.page_size,
            results=[],
            source_trace=trace,
            pagination_mode="page",
            is_complete=complete,
            completeness_reason=completeness_reason,
        )

    results: list[JurisprudenceResult] = []
    for card in cards:
        result = _parse_result_card(card, trace=trace, base_url=base_url)
        if result is not None:
            results.append(result)

    if not results and total > 0:
        raise ParserContractChangedError("TJGO/Projudi parser found total results but no cards")

    limited_results = results[: query.page_size]
    start = ((max(query.page, 1) - 1) * query.page_size) + 1 if limited_results else 0
    complete, completeness_reason = page_completeness(
        reported_total=total or None,
        start=start,
        returned=len(limited_results),
        total_is_authoritative=total > 0,
    )
    return SearchPage(
        source="tjgo_projudi_jurisprudencia",
        total=total or len(results),
        start=start,
        end=start + len(limited_results) - 1 if limited_results else 0,
        page=query.page,
        page_size=query.page_size,
        results=limited_results,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=completeness_reason,
    )


def tjgo_result_to_document(result: JurisprudenceResult) -> CanonicalDocument:
    """Build a canonical document from a TJGO result with embedded full text."""

    raw = dict(result.raw or {})
    text = str(raw.get("full_text") or result.summary or "")
    content_bytes = text.encode("utf-8")
    status = ExtractionStatus.COMPLETE if text.strip() else ExtractionStatus.EMPTY
    return CanonicalDocument(
        id=result.id,
        source=result.source,
        document_type=result.type,
        content_type="text/plain",
        title=f"TJGO/Projudi {result.type} {result.number}",
        text=text,
        url=raw.get("document_url"),
        sha256=hashlib.sha256(content_bytes).hexdigest(),
        byte_size=len(content_bytes),
        retrieved_at=result.source_trace.retrieved_at if result.source_trace else None,
        access_status=AccessStatus.PUBLIC,
        source_trace=result.source_trace,
        extraction_trace=ExtractionTrace(
            parser="tjgo_projudi_jurisprudencia.result_to_document",
            parser_version="1",
            status=status,
            access_status=AccessStatus.PUBLIC,
            content_sha256=hashlib.sha256(content_bytes).hexdigest(),
            content_bytes=len(content_bytes),
            metadata=raw,
        ),
        raw_metadata=raw,
    )


def _parse_result_card(
    card: Any, *, trace: SourceTrace, base_url: str
) -> JurisprudenceResult | None:
    card_text = _normalize_text(card.get_text("\n", strip=True))
    case_number = _first_match(CNJ_PATTERN, card_text)
    if not case_number:
        return None
    paragraphs = [_normalize_text(p.get_text(" ", strip=True)) for p in card.select("p")]
    paragraphs = [text for text in paragraphs if text]
    judging_body = paragraphs[0] if len(paragraphs) > 0 else None
    rapporteur = paragraphs[1] if len(paragraphs) > 1 else None
    decision_type = _normalize_decision_type(paragraphs[2] if len(paragraphs) > 2 else "decisao")
    publication_date = _extract_publication_date(card_text)
    full_text_element = card.select_one(".conteudoTexto")
    full_text = (
        _normalize_text(full_text_element.get_text(" ", strip=True))
        if full_text_element is not None
        else ""
    )
    file_id = _extract_file_id(card)
    document_url = (
        f"{base_url.rstrip('/')}/ConsultaJurisprudencia?Id_Arquivo={file_id}"
        if file_id
        else base_url.rstrip() + "/ConsultaJurisprudencia"
    )
    result_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
        source_url=document_url,
        limitations=trace.limitations,
    )
    return JurisprudenceResult(
        id=f"tjgo-projudi-{case_number}",
        source="tjgo_projudi_jurisprudencia",
        court="TJGO",
        type=decision_type,
        number=case_number,
        summary=full_text,
        full_text=full_text or None,
        rapporteur=rapporteur,
        updated_at=publication_date,
        highlights={},
        source_trace=result_trace,
        raw={
            "case_number": case_number,
            "judging_body": judging_body,
            "orgao_julgador": judging_body,
            "rapporteur": rapporteur,
            "magistrate": rapporteur,
            "decision_type": decision_type,
            "publication_date": publication_date,
            "data_publicacao": publication_date,
            "full_text": full_text,
            "document_url": document_url,
            "full_text_url": document_url,
            "file_id": file_id,
        },
    )


def _build_payload(query: JurisprudenceQuery) -> dict[str, str]:
    text = query.text or query.exact_phrase or query.number
    return {
        "PaginaAtual": str(query.page + 1),
        "PosicaoPaginaAtual": str(max(query.page - 1, 0)),
        "Viewstate": "",
        "Texto": text,
        "Id_Instancia": _map_instance(query),
        "Id_Area": "0",
        "Id_ServentiaSubTipo": "0",
        "Id_Serventia": "",
        "Id_Usuario": "",
        "Id_ArquivoTipo": _map_decision_type(query.types[0]) if query.types else "",
        "ProcessoNumero": query.number,
        "DataInicial": query.updated_from or query.published_from,
        "DataFinal": query.updated_to or query.published_to,
        "g-recaptcha-response": "",
        "Localizar": "Consultar",
    }


def _map_instance(query: JurisprudenceQuery) -> str:
    if not query.source_origin:
        return "0"
    normalized = _normalize_text(query.source_origin).lower()
    mapping = {
        "1": "16",
        "1g": "16",
        "1 grau": "16",
        "primeiro grau": "16",
        "tribunal": "15",
        "2 grau": "15",
        "segundo grau": "15",
        "turma recursal": "151",
        "turmas recursais": "151",
    }
    return mapping.get(normalized, query.source_origin)


def _map_decision_type(value: str) -> str:
    normalized = _normalize_text(value).lower()
    mapping = {
        "decisao": "4",
        "decisão": "4",
        "sentenca": "5",
        "sentença": "5",
        "acordao": "1",
        "acórdão": "1",
    }
    return mapping.get(normalized, value)


def _parse_total(soup: BeautifulSoup) -> int:
    text = soup.get_text(" ", strip=True)
    match = re.search(r"([\d.]+)\s+resultados encontrados", text, re.I)
    if not match:
        return 0
    return int(match.group(1).replace(".", ""))


def _extract_publication_date(text: str) -> str | None:
    return _first_match(
        re.compile(r"Publicado em\s+(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}:\d{2})?)", re.I), text
    )


def _extract_file_id(card: Any) -> str | None:
    for link in card.select("a[onclick]"):
        onclick = str(link.get("onclick") or "")
        match = FILE_ID_PATTERN.search(onclick)
        if match:
            return match.group("id")
    return None


def _normalize_decision_type(value: str) -> str:
    normalized = _normalize_text(value).lower()
    if "senten" in normalized:
        return "sentenca"
    if "ac" in normalized and "rd" in normalized:
        return "acordao"
    if "decis" in normalized:
        return "decisao"
    return normalized or "decisao"


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1 if pattern.groups else 0).strip() if match else None


def _decode_response_text(response: requests.Response) -> str:
    if response.encoding:
        return response.text
    return response.content.decode("iso-8859-1", errors="replace")


def _looks_like_blocked_page(html: str) -> bool:
    lowered = html.lower()
    has_results = "search-result" in lowered or "resultados encontrados" in lowered
    if has_results:
        return False
    blocking_markers = [
        "g-recaptcha",
        "token_desafio",
        "tokendesafio",
        "cloudflare ray id",
        "just a moment",
        "verifique que voce nao e um robo",
        "verifique que você não é um robô",
    ]
    return any(marker in lowered for marker in blocking_markers)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
