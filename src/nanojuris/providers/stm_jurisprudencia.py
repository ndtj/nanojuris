"""STM public jurisprudence provider."""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

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

PROCESS_NUMBER_RE = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
UUID_RE = re.compile(r"[a-f0-9]{32,64}", re.IGNORECASE)


class StmJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the public STM/JMU jurisprudence search."""

    name = "stm_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/consulta.php"
        params = _build_params(query)
        html, source_url = self._request_text("GET", endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=source_url,
            limitations=[
                "Consulta publica de jurisprudencia STM/JMU validada com requests limpo.",
                "A pagina publica retorna paineis HTML; start/rows sao enviados "
                "diretamente para a paginacao remota observada.",
                "O provider nao tenta contornar captcha, login ou controle de acesso.",
            ],
        )
        results = parse_stm_jurisprudencia_results(html, trace=trace, source_url=source_url)
        offset = max(query.page - 1, 0) * query.page_size
        reported_total = parse_stm_total_documents(html)
        total = reported_total if reported_total is not None else len(results)
        start = offset + 1 if results else 0
        complete, completeness_reason = page_completeness(
            reported_total=total,
            start=start,
            returned=len(results),
            total_is_authoritative=reported_total is not None,
        )
        return SearchPage(
            source=self.name,
            total=total,
            start=start,
            end=start + len(results) - 1 if results else 0,
            page=query.page,
            page_size=query.page_size,
            results=results,
            source_trace=trace,
            pagination_mode="offset",
            is_complete=complete,
            completeness_reason=completeness_reason,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document_id = _extract_document_id(precedent_id)
        endpoint = _full_text_url(document_id)
        content, source_url = self._request_text("GET", endpoint)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={"uuid": document_id},
            source_url=source_url,
            limitations=["Inteiro teor publico do STM/eproc vinculado ao resultado JMU."],
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": content, "content_type": "text/html"}],
            source_trace=trace,
            raw={"uuid": document_id},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        uuid = _extract_document_id(document_id)
        endpoint = _full_text_url(uuid)
        content, source_url = self._request_text("GET", endpoint)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={"uuid": uuid},
            source_url=source_url,
            limitations=["Documento publico retornado pela rota de inteiro teor STM/eproc."],
        )
        return CanonicalDocument(
            id=f"stm-jurisprudencia-document-{uuid}",
            source=self.name,
            document_type="acordao",
            content_type="text/html",
            title="STM inteiro teor",
            text=content,
            url=source_url,
            source_trace=trace,
            extraction_trace=ExtractionTrace(
                parser="stm_jurisprudencia.get_document",
                parser_version="1",
                status=ExtractionStatus.COMPLETE,
                access_status=AccessStatus.PUBLIC,
            ),
            raw_metadata={"uuid": uuid},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="STM Jurisprudencia JMU",
            source_url=self.config.stm_jurisprudencia_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range"],
            document_types=["acordao"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "case_class",
                "rapporteur",
                "subject",
                "judgment_date",
                "publication_date",
                "summary",
                "document_url",
                "uuid",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /consulta.php?search_filter_option=jurisprudencia&...",
                "GET https://eproc2g.stm.jus.br/eproc_2g_prod/externo_controlador.php?acao=visualizar_acordao&uuid=<uuid>",
            ],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            pagination_mode="offset",
            completeness_contract="reported_total_and_offset_window",
            supported_filters=["text", "number"],
            limitations=[
                "Busca publica descoberta em 2026-08-03 no portal JMU do STM.",
                "O provider envia start/rows e preserva o total exibido pela pagina publica.",
                "Facetas observadas no portal ainda nao sao filtros do modelo unificado.",
            ],
            responsible_use=[
                "Usar termos especificos e page_size pequeno em coletas exploratorias.",
                "Preservar UUID, URL de inteiro teor e SourceTrace para auditoria.",
                "Nao reutilizar cookies ou sessoes de navegador para contornar restricoes.",
            ],
        )

    def _request_text(self, method: str, path_or_url: str, **kwargs: Any) -> tuple[str, str]:
        self._respect_rate_limit()
        url = (
            path_or_url
            if path_or_url.startswith("http://") or path_or_url.startswith("https://")
            else urljoin(
                self.config.stm_jurisprudencia_url.rstrip("/") + "/",
                path_or_url.lstrip("/"),
            )
        )
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
                allow_redirects=True,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"STM jurisprudence request failed: {exc}") from exc

        response.encoding = response.encoding or "utf-8"
        text = response.text
        if response.status_code == 429:
            raise RateLimitDetectedError("STM jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("STM jurisprudence requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"STM jurisprudence returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"STM jurisprudence rejected request with HTTP {response.status_code}"
            )
        if _looks_like_access_control(text):
            raise AccessControlRequiredError("STM jurisprudence returned access-control HTML")
        return text, getattr(response, "url", url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def parse_stm_jurisprudencia_results(
    html: str,
    *,
    trace: SourceTrace,
    source_url: str,
) -> list[JurisprudenceResult]:
    """Parse STM/JMU public jurisprudence panels."""

    if _looks_like_access_control(html):
        raise AccessControlRequiredError("STM jurisprudence returned access-control HTML")

    soup = BeautifulSoup(html, "html.parser")
    panels = [
        panel
        for panel in soup.select("div.panel.panel-default")
        if panel.select_one('button[title="Exibir Inteiro Teor"], button[data-type]')
        and panel.select_one("dl")
    ]
    if not panels and _looks_like_empty_result(soup):
        return []
    if not panels:
        raise ParserContractChangedError("STM jurisprudence result panels not found")
    return [_parse_panel(panel, trace=trace, source_url=source_url) for panel in panels]


def _parse_panel(panel: Tag, *, trace: SourceTrace, source_url: str) -> JurisprudenceResult:
    labels = _extract_label_values(panel)
    text = _clean_text(panel.get_text(" ", strip=True))
    case_number = _find_process_number(text)
    if not case_number:
        raise ParserContractChangedError("STM jurisprudence case number not found")

    full_text_url = _extract_full_text_url(panel, source_url)
    uuid = _extract_uuid(full_text_url) or _first_data_uuid(panel)
    if not uuid:
        raise ParserContractChangedError("STM jurisprudence UUID not found")

    summary = _clean_text(_text(panel.select_one("blockquote")))
    body_text = _clean_text(_text(panel.select_one(".panel-body")))
    case_class = _extract_case_class(body_text, case_number)
    judgment_date = _extract_date(body_text, "Data de Julgamento")
    publication_date = _extract_date(body_text, "Data de Publicacao") or _extract_date(
        body_text, "Data de Publicação"
    )

    return JurisprudenceResult(
        id=f"stm-jurisprudencia-{uuid}",
        source="stm_jurisprudencia",
        court="STM",
        type="acordao",
        number=case_number,
        summary=summary,
        rapporteur=labels.get("relator(a)") or labels.get("relator"),
        updated_at=publication_date,
        source_trace=trace,
        raw={
            "uuid": uuid,
            "case_class": case_class,
            "subject": labels.get("assuntos"),
            "reviewer": labels.get("revisor(a)"),
            "judgment_date": judgment_date,
            "publication_date": publication_date,
            "document_url": full_text_url,
            "source_url": source_url,
            "labels": labels,
        },
    )


def _build_params(query: JurisprudenceQuery) -> dict[str, str]:
    offset = max(query.page - 1, 0) * query.page_size
    params = {
        "search_filter_option": "jurisprudencia",
        "search_filter": "busca_avancada",
        "q": query.text or "*",
        "start": str(offset),
        "rows": str(query.page_size),
    }
    if query.exact_phrase:
        params["fqx_ementa"] = query.exact_phrase
    elif query.text:
        params["fqx_ementa"] = query.text
    if query.number:
        params["fqx_numero_jurisprudencia"] = query.number
    if query.published_from:
        params["fqx_data_publicacao_inicio"] = query.published_from
    if query.published_to:
        params["fqx_data_publicacao_fim"] = query.published_to
    if query.updated_from:
        params["fqx_data_decisao_inicio"] = query.updated_from
    if query.updated_to:
        params["fqx_data_decisao_fim"] = query.updated_to
    return params


def parse_stm_total_documents(html: str) -> int | None:
    """Extract the public result count shown by the STM result page."""

    text = _clean_text(BeautifulSoup(html, "html.parser").get_text(" ", strip=True))
    match = re.search(r"\d+\s*-\s*\d+\s+de\s+([\d.]+)\s+documentos", text, re.IGNORECASE)
    if not match:
        return None
    try:
        return int(match.group(1).replace(".", ""))
    except ValueError:
        return None


def _extract_label_values(panel: Tag) -> dict[str, str]:
    labels: dict[str, str] = {}
    for dl in panel.select("dl"):
        children = [child for child in dl.find_all(["dt", "dd"], recursive=False)]
        for index in range(0, len(children) - 1, 2):
            label = _clean_label(children[index].get_text(" ", strip=True))
            value = _clean_text(children[index + 1].get_text(" ", strip=True))
            if label and value:
                labels[label] = value
    return labels


def _extract_full_text_url(panel: Tag, source_url: str) -> str | None:
    button = panel.select_one('button[title="Exibir Inteiro Teor"]')
    raw_onclick = button.get("onclick") if button else ""
    onclick = raw_onclick if isinstance(raw_onclick, str) else ""
    match = re.search(r"openInteiroTeor\(['\"]([^'\"]+)", onclick or "")
    if not match:
        return None
    return urljoin(source_url, match.group(1).replace("&amp;", "&"))


def _extract_uuid(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    uuid = parse_qs(parsed.query).get("uuid", [None])[0]
    if uuid and UUID_RE.fullmatch(uuid):
        return uuid
    match = UUID_RE.search(url)
    return match.group(0) if match else None


def _first_data_uuid(panel: Tag) -> str | None:
    button = panel.select_one("button[data-uuid]")
    raw_value = button.get("data-uuid") if button else None
    value = raw_value if isinstance(raw_value, str) else None
    return value if value and UUID_RE.fullmatch(value) else None


def _extract_document_id(precedent_id: str) -> str:
    candidate = precedent_id.removeprefix("stm-jurisprudencia-document-").removeprefix(
        "stm-jurisprudencia-"
    )
    if not UUID_RE.fullmatch(candidate):
        raise ParserContractChangedError(f"Invalid STM jurisprudence id: {precedent_id!r}")
    return candidate


def _full_text_url(uuid: str) -> str:
    return (
        "https://eproc2g.stm.jus.br/eproc_2g_prod/externo_controlador.php"
        f"?acao=visualizar_acordao&uuid={uuid}"
    )


def _find_process_number(text: str) -> str | None:
    match = PROCESS_NUMBER_RE.search(text)
    return match.group(0) if match else None


def _extract_case_class(body_text: str, case_number: str) -> str | None:
    start = body_text.find(case_number)
    if start < 0:
        return None
    tail = body_text[start + len(case_number) :]
    marker = re.search(r"\bN\.?[ºo]?\s*" + re.escape(case_number), tail, re.IGNORECASE)
    if marker:
        value = tail[: marker.start()].strip()
        tokens = value.split()
        midpoint = len(tokens) // 2
        if midpoint and tokens[:midpoint] == tokens[midpoint:]:
            tokens = tokens[:midpoint]
        return _clean_text(" ".join(tokens)) or None
    return None


def _extract_date(text: str, label: str) -> str | None:
    match = re.search(re.escape(label) + r":\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
    return match.group(1) if match else None


def _looks_like_access_control(html: str) -> bool:
    lowered = html.lower()
    markers = ["g-recaptcha", "recaptcha", "captcha", "cf-challenge", "login"]
    return any(marker in lowered for marker in markers)


def _looks_like_empty_result(soup: BeautifulSoup) -> bool:
    text = soup.get_text(" ", strip=True).lower()
    normalized_text = _strip_accents(text)
    markers = [
        "nao foram encontrados",
        "nenhum resultado",
        "nenhum registro",
        "sua pesquisa nao encontrou",
        "nao ha resultados",
    ]
    if any(marker in normalized_text for marker in markers):
        return True
    return "não foram encontrados" in text or "nao foram encontrados" in text


def _clean_label(value: str) -> str:
    return _clean_text(value).rstrip(":").lower()


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _text(node: Tag | None) -> str:
    return node.get_text(" ", strip=True) if node else ""
