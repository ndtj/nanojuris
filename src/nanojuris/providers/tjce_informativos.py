"""TJCE curated jurisprudence informativos provider."""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

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

CNJ_PATTERN = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")


class TjceInformativosProvider(JurisprudenceProvider):
    """Provider for the public TJCE curated informativos page."""

    name = "tjce_informativos"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/informativo-jurisprudencia/"
        params = _query_params(query)
        html, final_url = self._request_text(endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /informativo-jurisprudencia/",
            query=params,
            source_url=final_url,
            limitations=[
                "Informativo curado do TJCE; a propria fonte informa que nao e "
                "repositorio oficial integral nem necessariamente o posicionamento prevalente.",
                "O destaque e uma sintese editorial e nao equivale ao inteiro teor do acordao.",
                "Links de processo e de leitura completa sao preservados no raw.",
            ],
        )
        return parse_tjce_informativos(
            html,
            query=query,
            trace=trace,
            base_url=self.config.tjce_informativos_url,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[],
            raw={
                "message": "TJCE Informativos expose curated highlights and official links; "
                "they do not replace the full judgment repository."
            },
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJCE Informativos de Jurisprudencia",
            source_url=(
                self.config.tjce_informativos_url.rstrip("/") + "/informativo-jurisprudencia/"
            ),
            category="curated_jurisprudence",
            search_modes=["text", "edition_number", "metadata", "curated_catalog"],
            document_types=["informativo_item"],
            content_formats=["html", "pdf"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "edition_number",
                "edition_date",
                "case_number",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "law_branch",
                "subject",
                "summary",
                "document_url",
                "case_url",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=["GET /informativo-jurisprudencia/"],
            supports_full_text=False,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_suggestions=False,
            supports_live_tests=True,
            pagination_mode="local_window",
            completeness_contract="observed_edition_window",
            full_text_access="not_available",
            supported_filters=[
                "text",
                "number",
                "types",
                "published_from",
                "published_to",
                "page",
            ],
            limitations=[
                "A busca textual e a busca de edicao dependem do formulario WordPress publico.",
                "A pagina mistura ultima edicao e edicoes anteriores; a edicao e "
                "preservada por item.",
                "A fonte nao deve ser descrita como repositorio integral de acordaos do TJCE.",
            ],
            responsible_use=[
                "Citar o informativo, o item, o processo e a URL oficial.",
                "Nao converter destaque editorial em tese vinculante ou regra geral.",
                "Usar rate limit e preservar o escopo curado no MCP e no Studio.",
            ],
        )

    def _request_text(self, path: str, **kwargs: Any) -> tuple[str, str]:
        self._respect_rate_limit()
        url = urljoin(self.config.tjce_informativos_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        try:
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJCE Informativos request failed: {exc}") from exc
        status = int(getattr(response, "status_code", 0) or 0)
        text = str(getattr(response, "text", "") or "")
        if status in {401, 403} or _looks_like_access_control(text):
            raise AccessControlRequiredError("TJCE Informativos returned access-control response")
        if status == 429:
            raise RateLimitDetectedError("TJCE Informativos returned HTTP 429")
        if status >= 500:
            raise SourceUnavailableError(f"TJCE Informativos returned HTTP {status}")
        if status >= 400:
            raise SourceUnavailableError(f"TJCE Informativos returned HTTP {status}")
        response.encoding = response.encoding or response.apparent_encoding or "utf-8"
        self._last_request = time.monotonic()
        return response.text, str(getattr(response, "url", "") or url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)


def parse_tjce_informativos(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    """Parse current and previous TJCE informativo editions."""

    soup = BeautifulSoup(html, "html.parser")
    panes = soup.select("article.content .tab-pane")
    if not panes:
        text = _normalize_text(soup.get_text(" ", strip=True))
        if "nenhum" in text.lower() or "sem resultado" in text.lower():
            return _empty_page(query, trace, "A fonte informou resultado vazio.")
        raise ParserContractChangedError("TJCE Informativos tab panes not found")
    results: list[JurisprudenceResult] = []
    for pane in panes:
        edition_number, edition_date = _edition_metadata(pane)
        for table in pane.select("table"):
            result = _parse_table(
                table,
                edition_number=edition_number,
                edition_date=edition_date,
                trace=trace,
                base_url=base_url,
            )
            if result is not None:
                results.append(result)
    if not results:
        return _empty_page(query, trace, "As edicoes do TJCE nao possuem itens na pagina.")
    start_index = (query.page - 1) * query.page_size
    page_results = results[start_index : start_index + query.page_size]
    start = start_index + 1 if page_results else 0
    complete, reason = page_completeness(
        reported_total=len(results),
        start=start,
        returned=len(page_results),
        total_is_authoritative=False,
    )
    return SearchPage(
        source="tjce_informativos",
        total=len(results),
        start=start,
        end=start + len(page_results) - 1 if page_results else 0,
        page=query.page,
        page_size=query.page_size,
        results=page_results,
        source_trace=trace,
        pagination_mode="local_window",
        is_complete=complete,
        completeness_reason=reason,
    )


def _parse_table(
    table: Tag,
    *,
    edition_number: str | None,
    edition_date: str | None,
    trace: SourceTrace,
    base_url: str,
) -> JurisprudenceResult | None:
    values: dict[str, str] = {}
    for row in table.select("tr"):
        cells = row.select("th, td")
        if len(cells) < 2:
            continue
        label = _normalize_text(cells[0].get_text(" ", strip=True)).lower().rstrip(":")
        values[label] = _normalize_text(cells[1].get_text(" ", strip=True))
    process_cell = next(
        (cell for cell in table.select("td") if CNJ_PATTERN.search(cell.get_text(" ", strip=True))),
        None,
    )
    if process_cell is None:
        return None
    process_text = _normalize_text(process_cell.get_text(" ", strip=True))
    case_number = CNJ_PATTERN.search(process_text)
    if case_number is None:
        return None
    case_number_value = case_number.group(0)
    rapporteur, judging_body, judgment_date_raw = _parse_process_metadata(process_text)
    container = table.find_parent(class_="espacamento-itens") or table.parent
    detail = (
        container.select_one("a[href*='/informativo-jurisprudencia/jurisprudencia/']")
        if isinstance(container, Tag)
        else None
    )
    detail_url = urljoin(base_url.rstrip("/") + "/", str(detail["href"])) if detail else None
    stable = hashlib.sha256(
        f"{edition_number}|{case_number_value}|{detail_url}|{judgment_date_raw}".encode()
    ).hexdigest()[:20]
    result_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
        source_url=detail_url or trace.source_url,
        limitations=trace.limitations,
    )
    judgment_date = _parse_br_date(judgment_date_raw)
    summary = values.get("destaque", "")
    return JurisprudenceResult(
        id=f"tjce-informativo-{stable}",
        source="tjce_informativos",
        court="TJCE",
        type="informativo_item",
        number=case_number_value,
        summary=summary or None,
        judgment_date=judgment_date,
        publication_date=edition_date,
        rapporteur=rapporteur,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=result_trace,
        raw={
            "edition_number": edition_number,
            "edition_date": edition_date,
            "case_number": case_number_value,
            "rapporteur": rapporteur,
            "judging_body": judging_body,
            "judgment_date": judgment_date,
            "judgment_date_raw": judgment_date_raw,
            "law_branch": values.get("ramo do direito") or values.get("ramos do direito"),
            "subject": values.get("assunto"),
            "summary": summary,
            "document_url": detail_url,
            "case_url": _case_url(process_cell),
            "curated_source": True,
        },
    )


def _edition_metadata(pane: Tag) -> tuple[str | None, str | None]:
    text = _normalize_text(
        " ".join(x.get_text(" ", strip=True) for x in pane.select(".informativo"))
    )
    number_match = re.search(r"Informativo\s+n[º°o]?\s*(\d+)", text, re.IGNORECASE)
    date_match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", text)
    return (
        number_match.group(1) if number_match else None,
        _parse_br_date(date_match.group(1)) if date_match else None,
    )


def _parse_process_metadata(text: str) -> tuple[str | None, str | None, str | None]:
    remainder = text.split("Processo", 1)[-1]
    remainder = re.sub(CNJ_PATTERN, "", remainder, count=1).strip(" ,")
    judgment_match = re.search(r"Julgado em\s+(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
    before_date = remainder[
        : judgment_match.start() - text.find("Processo") if judgment_match else len(remainder)
    ]
    parts = [part.strip(" ,") for part in before_date.split(",") if part.strip(" ,")]
    rapporteur = parts[0] if parts else None
    judging_body = parts[1] if len(parts) > 1 else None
    return rapporteur, judging_body, judgment_match.group(1) if judgment_match else None


def _case_url(cell: Tag) -> str | None:
    link = cell.select_one("a[href]")
    return str(link["href"]) if link else None


def _query_params(query: JurisprudenceQuery) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if query.text or query.exact_phrase:
        params["busca_livre"] = query.text or query.exact_phrase
    if query.types:
        params["tipos_edicao[]"] = query.types
    if query.number:
        params["numero_edicao"] = query.number
    if query.published_from or query.updated_from:
        params["data_publicacao_inicial"] = query.published_from or query.updated_from
    if query.published_to or query.updated_to:
        params["data_publicacao_final"] = query.published_to or query.updated_to
    return params


def _parse_br_date(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"\d{2}/\d{2}/\d{4}", value)
    if not match:
        return None
    return datetime.strptime(match.group(0), "%d/%m/%Y").date().isoformat()


def _normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _looks_like_access_control(text: str) -> bool:
    soup = BeautifulSoup(text, "html.parser")
    for element in soup.select("script, style, noscript"):
        element.decompose()
    normalized = _normalize_text(soup.get_text(" ", strip=True)).lower()
    return any(
        marker in normalized
        for marker in (
            "acesso negado",
            "access denied",
            "verifique que voce nao e um robo",
            "challenge-error-text",
        )
    )


def _empty_page(query: JurisprudenceQuery, trace: SourceTrace, reason: str) -> SearchPage:
    return SearchPage(
        source="tjce_informativos",
        total=0,
        start=0,
        end=0,
        page=query.page,
        page_size=query.page_size,
        results=[],
        source_trace=trace,
        pagination_mode="local_window",
        is_complete=True,
        completeness_reason=reason,
    )
