"""TJTO public Jurisprudencia 4.0 provider."""

from __future__ import annotations

import hashlib
import html
import re
import time
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from nanojuris.canonical import normalize_date
from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import build_canonical_document
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
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

PROCESS_NUMBER_RE = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
UUID_RE = re.compile(r"uuid=([0-9a-f]{16,})", re.IGNORECASE)
TOTAL_RE = re.compile(r"\(([\d.]+)\s+resultados?\)", re.IGNORECASE)
TJTO_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
)


class TjtoJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for TJTO's public HTML search and document routes."""

    name = "tjto_jurisprudencia"

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
        return self.config.tjto_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        term = query.text or query.exact_phrase or query.number
        if not term:
            raise ValueError("TJTO jurisprudence search requires text, exact_phrase or number")
        page_size = _page_size(query.page_size)
        form = build_tjto_search_parameters(query, page_size=page_size)
        content, source_url = self._request_html("POST", "/consulta.php", data=form)
        trace = SourceTrace(
            provider=self.name,
            endpoint="POST /consulta.php",
            query={
                "text": query.text,
                "exact_phrase": query.exact_phrase,
                "number": query.number,
                "page": query.page,
                "page_size": page_size,
                "form": {key: value for key, value in form.items() if "fq_" not in key},
            },
            source_url=source_url,
            limitations=[
                "A fonte exige User-Agent de navegador como parte do contrato HTTP publico.",
                "Filtros de classe, assunto e competencia sao expostos pelo formulario, mas "
                "a query comum ainda nao possui campos tipados para esses valores.",
                "O link visualizado como 'Inteiro Teor' redireciona para documento.php e foi "
                "validado como HTML completo, nao como PDF.",
            ],
            **self._last_http_metadata,
        )
        page = parse_tjto_search_response(content, query=query, trace=trace)
        if query.fetch_details:
            for result in page.results:
                document_url = result.raw.get("document_url")
                document_id = result.raw.get("document_uuid")
                if not document_id:
                    result.extraction_status = ExtractionStatus.PARTIAL
                    continue
                document = self.get_document(str(document_id))
                result.full_text = document.text
                result.raw["full_text"] = document.text
                result.raw["full_text_status"] = "loaded" if document.text else "empty"
                result.raw["content_sha256"] = document.sha256
                result.raw["response_bytes"] = document.byte_size
                result.raw["document_content_type"] = document.content_type
                result.raw["document_url"] = document.url or document_url
                result.extraction_status = document.extraction_status
        return page

    def get_document(self, document_id: str):
        uuid = document_id.removeprefix("tjto-jurisprudencia-")
        if not re.fullmatch(r"[0-9a-f]{16,}", uuid, re.IGNORECASE):
            raise ValueError("TJTO document_id must contain the public document uuid")
        content, source_url = self._request_html(
            "GET", "/documento.php", params={"uuid": uuid, "options": "#page=1"}
        )
        if b"<html" not in content[:4096].lower() and b"<fieldset" not in content[:4096].lower():
            raise ParserContractChangedError("TJTO document response is not HTML")
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /documento.php",
            query={"document_id": uuid},
            source_url=source_url,
            limitations=["Documento publico entregue pela rota oficial documento.php."],
            **self._last_http_metadata,
        )
        return build_canonical_document(
            document_id=f"tjto-jurisprudencia-{uuid}",
            source=self.name,
            document_type="inteiro_teor",
            content=content,
            content_type=self._last_http_metadata.get("content_type"),
            url=source_url,
            title=None,
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"document_endpoint": "/documento.php", "uuid": uuid},
            parser="tjto.documento_html",
            parser_version="1",
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise NotImplementedError(
            "TJTO expoe o inteiro teor como CanonicalDocument; nao ha DecisionBundle separado."
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJTO Jurisprudencia 4.0",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "facets", "pagination"],
            document_types=["acordao", "decisao_monocratica", "sentenca"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "case_number",
                "case_class",
                "decision_type",
                "subject",
                "competence",
                "rapporteur",
                "judgment_date",
                "filing_date",
                "summary",
                "document_url",
                "document_uuid",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.ACCESS_CONTROL_REQUIRED],
            endpoints=[
                "GET /consulta.php",
                "POST /consulta.php",
                "GET /documento.php?uuid=<uuid>",
            ],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_live_tests=True,
            pagination_mode="offset",
            max_remote_page_size=100,
            completeness_contract="reported_html_total_and_start_rows_window",
            full_text_access="detail_call",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "rapporteur",
                "source_origin",
                "types",
                "order_by",
                "page",
                "fetch_details",
            ],
            limitations=[
                "A busca textual e os metadados sao HTML e dependem do layout publico.",
                "O total remoto e lido do contador textual da pagina quando presente.",
                "O formulario possui filtros adicionais de classe, assunto e competencia; "
                "eles ainda aguardam campos tipados na query unificada.",
            ],
            responsible_use=[
                "Usar User-Agent normal, rate limit e page_size moderado.",
                "Carregar documento sob demanda; nao baixar o corpus inteiro automaticamente.",
                "Nao confundir ementa com o HTML de inteiro teor carregado por documento.php.",
            ],
        )

    def _request_html(self, method: str, path: str, **kwargs: Any) -> tuple[bytes, str]:
        self._respect_rate_limit()
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": TJTO_BROWSER_USER_AGENT,
        }
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
            raise SourceUnavailableError(f"TJTO jurisprudence request failed: {exc}") from exc
        content = bytes(getattr(response, "content", b"") or response.text.encode("utf-8"))
        response_url = str(getattr(response, "url", url) or url)
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": response_url,
            "content_type": (getattr(response, "headers", {}) or {}).get("Content-Type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        if response.status_code == 429:
            raise RateLimitDetectedError("TJTO jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJTO jurisprudence requires access validation")
        if response.status_code in {400, 422}:
            raise QueryRejectedError(
                f"TJTO jurisprudence rejected the query with HTTP {response.status_code}"
            )
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJTO jurisprudence returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJTO jurisprudence rejected request with HTTP {response.status_code}"
            )
        return content, response_url

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def build_tjto_search_parameters(
    query: JurisprudenceQuery, *, page_size: int | None = None
) -> dict[str, str]:
    """Build the form fields observed in the public TJTO search form."""

    size = _page_size(page_size or query.page_size)
    term = query.text or query.exact_phrase or query.number
    form: dict[str, str] = {
        "q": term,
        "start": str(max(query.page - 1, 0) * size),
        "rows": str(size),
        "type_minuta_selected": "1",
    }
    if query.exact_phrase:
        form["soementa"] = "on"
    if query.number:
        form["numero_processo"] = query.number
    if query.source_origin:
        form["tip_criterio_inst"] = query.source_origin
    if query.order_by:
        form["tip_criterio_data"] = _order_value(query.order_by)
    selected_types = {item.lower() for item in query.types}
    if not selected_types or "acordao" in selected_types or "acórdão" in selected_types:
        form["tipo_decisao_acordao"] = "true"
    if "sentenca" in selected_types or "sentença" in selected_types:
        form["tipo_decisao_sentenca"] = "true"
    if (
        "decisao" in selected_types
        or "decisão" in selected_types
        or "monocratica" in selected_types
    ):
        form["dec_monocrativa_is2G_true"] = "true"
    if query.rapporteur:
        form[f"fq_magistrado[{query.rapporteur}]"] = "on"
    return form


def parse_tjto_search_response(
    content: bytes, *, query: JurisprudenceQuery, trace: SourceTrace
) -> SearchPage:
    """Parse one public TJTO HTML window without discarding the card HTML."""

    soup = BeautifulSoup(content, "html.parser")
    cards = soup.select("div.container.align-self-center.panel.panel-default")
    total = _parse_total(soup.get_text(" ", strip=True))
    if not cards and total:
        raise ParserContractChangedError("TJTO result total exists but result cards were not found")
    results = [_card_to_result(card, trace=trace) for card in cards]
    page_size = _page_size(query.page_size)
    start = (max(query.page - 1, 0) * page_size) + 1 if results else 0
    complete, reason = page_completeness(
        reported_total=total or len(results),
        start=start,
        returned=len(results),
        total_is_authoritative=total is not None,
    )
    return SearchPage(
        source="tjto_jurisprudencia",
        total=total or len(results),
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


def _card_to_result(card: Any, *, trace: SourceTrace) -> JurisprudenceResult:
    heading_node = card.select_one(".panel_doc")
    heading = _clean_text(heading_node.get_text(" ", strip=True)) if heading_node else ""
    body = card.select_one(".panel-body")
    if body is None:
        raise ParserContractChangedError("TJTO result card has no panel-body")
    body_text = _clean_text(body.get_text(" ", strip=True))
    number_match = PROCESS_NUMBER_RE.search(heading)
    number = number_match.group(0) if number_match else None
    document_link = card.select_one("a.button_doc")
    onclick = html.unescape(str(document_link.get("onclick", ""))) if document_link else ""
    uuid_match = UUID_RE.search(onclick)
    stable_id = uuid_match.group(1) if uuid_match else number
    if not stable_id:
        raise ParserContractChangedError("TJTO result card has no stable uuid or process number")
    values = _extract_labeled_fields(body_text)
    summary = values.get("summary") or None
    result = JurisprudenceResult(
        id=f"tjto-jurisprudencia-{stable_id}",
        source="tjto_jurisprudencia",
        court="TJTO",
        type=values.get("decision_type") or "jurisprudencia",
        number=number,
        summary=summary,
        rapporteur=values.get("rapporteur") or None,
        judgment_date=normalize_date(values.get("judgment_date")),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if summary else ExtractionStatus.PARTIAL,
        source_trace=trace,
        raw={
            "card_html": str(card),
            "case_class": values.get("case_class"),
            "subject": values.get("subject"),
            "competence": values.get("competence"),
            "filing_date": values.get("filing_date"),
            "judgment_date": values.get("judgment_date"),
            "document_uuid": uuid_match.group(1) if uuid_match else None,
            "document_url": (
                urljoin(trace.source_url or "", f"/documento.php?uuid={uuid_match.group(1)}")
                if uuid_match
                else None
            ),
        },
    )
    return result


def _extract_labeled_fields(text: str) -> dict[str, str]:
    labels = {
        "case_class": r"Classe\s+(.*?)\s+Tipo Julgamento",
        "decision_type": r"Tipo Julgamento\s+(.*?)\s+Assunto\(s\)",
        "subject": r"Assunto\(s\)\s+(.*?)\s+Competência",
        "competence": r"Competência\s+(.*?)\s+(?:Relator|Juiz)\s+",
        "rapporteur": r"(?:Relator|Juiz)\s+(.*?)\s+Data Autuação",
        "filing_date": r"Data Autuação\s+(.*?)\s+Data Julgamento",
        "judgment_date": r"Data Julgamento\s+(.*?)\s+EMENTA(?:\.|:)",
        "summary": r"EMENTA(?:\.|:)\s+(.*?)(?:\s+Referências?|$)",
    }
    return {
        key: _clean_text(match.group(1))
        for key, pattern in labels.items()
        if (match := re.search(pattern, text, re.I | re.S))
    }


def _parse_total(text: str) -> int | None:
    match = TOTAL_RE.search(_clean_text(text))
    if not match:
        return None
    try:
        return int(match.group(1).replace(".", ""))
    except ValueError:
        return None


def _order_value(value: str) -> str:
    normalized = value.lower()
    if "old" in normalized or normalized.endswith("asc"):
        return "ASC"
    if "relev" in normalized:
        return "RELEV"
    return "DESC"


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 100))
