"""TJPR public jurisprudence search provider."""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests

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
from nanojuris.parsing import HtmlNode, parse_html
from nanojuris.providers.base import JurisprudenceProvider

CNJ_PATTERN = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
DATE_PATTERN = re.compile(r"\d{2}/\d{2}/\d{4}")
SESSION_ID_PATTERN = re.compile(r";jsessionid=[^?#/]+", re.IGNORECASE)


class TjprJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the public TJPR jurisprudence HTML search."""

    name = "tjpr_jurisprudencia"

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
        endpoint = "/jurisprudencia/publico/pesquisa.do?actionType=pesquisarRefinado&filtro=true"
        html, final_url = self._search_html(query, endpoint)
        trace = SourceTrace(
            provider=self.name,
            endpoint="POST /jurisprudencia/publico/pesquisa.do?actionType=pesquisar",
            query={
                "criterioPesquisa": query.text or query.exact_phrase or query.number,
                "processo": query.number,
                "dataPublicacaoInicio": query.published_from,
                "dataPublicacaoFim": query.published_to,
                "dataJulgamentoInicio": query.updated_from,
                "dataJulgamentoFim": query.updated_to,
                "page": query.page,
                "page_size": query.page_size,
            },
            source_url=final_url,
            limitations=[
                "Fonte HTML publica do TJPR sujeita a mudancas de layout.",
                "A busca publica tambem apresenta uma secao separada da Corte IDH; "
                "ela nao e convertida neste provider em jurisprudencia TJPR.",
                "O resultado pode indicar segredo de justica ou conteudo pendente; "
                "o provider preserva o status sem inferir inteiro teor.",
            ],
            **self._last_http_metadata,
        )
        return parse_tjpr_results(
            html,
            query=query,
            trace=trace,
            base_url=self.config.tjpr_jurisprudencia_url,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise NotImplementedError(
            "TJPR exige o link de detalhe retornado pela pesquisa; nao e seguro "
            "reconstruir o slug a partir de um identificador isolado."
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJPR Jurisprudencia",
            source_url=self.config.tjpr_jurisprudencia_url,
            category="court_jurisprudence",
            search_modes=["full_text", "case_number", "date_range", "metadata"],
            document_types=["acordao", "decisao_monocratica", "decisao"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "source_record_id",
                "case_number",
                "decision_type",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "summary",
                "document_url",
                "secret_or_pending_content",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /jurisprudencia/publico/pesquisa.do?actionType=pesquisarRefinado&filtro=true",
                "POST /jurisprudencia/publico/pesquisa.do?actionType=pesquisar",
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
            completeness_contract="reported_tjpr_window",
            full_text_access="not_available",
            supported_filters=[
                "text",
                "number",
                "published_from",
                "published_to",
                "updated_from",
                "updated_to",
            ],
            limitations=[
                "Filtros de classe, relator, comarca, orgao e assunto exigem IDs "
                "obtidos pelos controles da propria pagina e ainda nao sao inferidos.",
                "O link de detalhe deve ser preservado da resposta; o provider nao monta slug.",
                "O texto retornado nesta superficie e ementa/resumo; nao equivale ao inteiro teor.",
            ],
            responsible_use=[
                "Usar paginas pequenas e respeitar rate limit local.",
                "Nao tentar acessar a area restrita nem contornar captcha ou sessao.",
                "Preservar SourceTrace, URL oficial e campos de acesso parcial.",
            ],
        )

    def _search_html(self, query: JurisprudenceQuery, endpoint: str) -> tuple[str, str]:
        self._respect_rate_limit()
        initial_url = urljoin(
            self.config.tjpr_jurisprudencia_url.rstrip("/") + "/", endpoint.lstrip("/")
        )
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        try:
            initial = self.session.get(
                initial_url,
                headers=headers,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
            _raise_for_tjpr_response(initial, "TJPR initial search")
            form = parse_html(initial.content, base_url=initial.url).select_one("form#pesquisaForm")
            if form is None or not form.get("action"):
                raise ParserContractChangedError("TJPR search form pesquisaForm not found")
            payload = _form_payload(form)
            payload.update(_query_payload(query))
            action = urljoin(initial.url, str(form["action"]))
            response = self.session.post(
                action,
                data=payload,
                headers={**headers, "Referer": initial.url},
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
            _raise_for_tjpr_response(response, "TJPR search")
        except (ParserContractChangedError, AccessControlRequiredError):
            raise
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPR search request failed: {exc}") from exc
        self._last_request = time.monotonic()
        content = bytes(getattr(response, "content", b"") or response.text.encode("utf-8"))
        headers_received = getattr(response, "headers", {}) or {}
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": getattr(response, "url", action),
            "content_type": headers_received.get("Content-Type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        return response.text, _strip_session_id(response.url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)


def parse_tjpr_results(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    """Parse TJPR's public result table without including Corte IDH rows."""

    document = parse_html(html, base_url=base_url)
    table = document.select_one("table.resultTable.jurisprudencia")
    if table is None:
        text = _normalize_text(document.text())
        if _is_explicit_empty(text) and not _looks_like_access_control(text):
            return _empty_page(query, trace, "A fonte respondeu sem registros TJPR.")
        if _looks_like_access_control(text):
            raise AccessControlRequiredError("TJPR returned an access-control page")
        raise ParserContractChangedError("TJPR jurisprudence result table not found")

    total = _parse_total(document.text())
    rows = [row for row in table.select("tr") if _is_tjpr_row(row)]
    results: list[JurisprudenceResult] = []
    for index, row in enumerate(rows, start=1):
        result = _parse_tjpr_row(row, trace=trace, base_url=base_url, index=index)
        if result is not None:
            results.append(result)
    if rows and not results:
        raise ParserContractChangedError("TJPR rows found but no decision fields were parsed")

    limited = results[: query.page_size]
    start = ((query.page - 1) * query.page_size) + 1 if limited else 0
    complete, reason = page_completeness(
        reported_total=total or None,
        start=start,
        returned=len(limited),
        total_is_authoritative=total > 0,
    )
    return SearchPage(
        source="tjpr_jurisprudencia",
        total=total or len(results),
        start=start,
        end=start + len(limited) - 1 if limited else 0,
        page=query.page,
        page_size=query.page_size,
        results=limited,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=reason,
    )


def _parse_tjpr_row(
    row: HtmlNode,
    *,
    trace: SourceTrace,
    base_url: str,
    index: int,
) -> JurisprudenceResult | None:
    link = row.select_one("a[href*='/jurisprudencia/j/']")
    if link is None:
        return None
    row_text = _normalize_text(row.get_text(" ", strip=True))
    case_number = _first_match(CNJ_PATTERN, row_text)
    source_id = _input_value(row, "idsSelecionados")
    if not source_id:
        source_id = case_number or hashlib.sha256(row_text.encode("utf-8")).hexdigest()[:16]
    decision_type = _extract_parenthesized_type(link, row_text)
    judgment_raw = _label_value(row_text, "Data Julgamento:")
    judgment_date = _parse_br_date(judgment_raw)
    document_url = urljoin(base_url.rstrip("/") + "/", str(link["href"]))
    document_url = _strip_session_id(document_url)
    summary_cell = row.select_one("td.juris-tabela-ementa")
    summary = _normalize_text(summary_cell.get_text(" ", strip=True)) if summary_cell else ""
    rapporteur: str | None = _label_value(row_text, "Relator:")
    rapporteur = _truncate_at_labels(rapporteur)
    judging_body: str | None = _label_value(row_text, "Órgão Julgador:")
    judging_body = _truncate_at_labels(judging_body)
    secret = "Segredo de Justiça" in row_text
    pending = "Conteúdo pendente de análise e liberação" in row_text
    access_status = AccessStatus.PARTIAL if secret or pending else AccessStatus.PUBLIC
    result_trace = SourceTrace(
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
        retrieval_status=trace.retrieval_status,
    )
    return JurisprudenceResult(
        id=f"tjpr-{source_id}",
        source="tjpr_jurisprudencia",
        court="TJPR",
        type=decision_type,
        number=case_number,
        summary=summary or None,
        rapporteur=rapporteur,
        judgment_date=judgment_date,
        access_status=access_status,
        extraction_status=ExtractionStatus.PARTIAL if pending else ExtractionStatus.COMPLETE,
        source_trace=result_trace,
        raw={
            "source_record_id": source_id,
            "case_number": case_number,
            "decision_type": decision_type,
            "rapporteur": rapporteur,
            "judging_body": judging_body,
            "judgment_date": judgment_date,
            "judgment_date_raw": judgment_raw,
            "document_url": document_url,
            "secret_or_pending_content": secret or pending,
            "secret_of_justice": secret,
            "content_pending_release": pending,
            "row_text": row_text,
            "source_row_index": index,
        },
    )


def _form_payload(form: HtmlNode) -> dict[str, str]:
    payload: dict[str, str] = {}
    for field in form.select("input[name]"):
        field_type = str(field.get("type") or "text").lower()
        if field_type in {"button", "submit", "checkbox", "radio"}:
            continue
        name = field.get("name")
        if name:
            payload[name] = str(field.get("value") or "")
    return payload


def _query_payload(query: JurisprudenceQuery) -> dict[str, str]:
    return {
        "criterioPesquisa": query.text or query.exact_phrase or query.number,
        "processo": query.number,
        "dataPublicacaoInicio": query.published_from,
        "dataPublicacaoFim": query.published_to,
        "dataJulgamentoInicio": query.updated_from,
        "dataJulgamentoFim": query.updated_to,
        "pageSize": str(min(query.page_size, 50)),
        "pageNumber": str(query.page),
        "page": str(query.page),
        "sortColumn": "id",
        "sortOrder": "desc",
    }


def _is_tjpr_row(row: HtmlNode) -> bool:
    return bool(
        row.select_one("input[name='idsSelecionados']")
        and row.select_one("a[href*='/jurisprudencia/j/']")
    )


def _input_value(row: HtmlNode, name: str) -> str | None:
    field = row.select_one(f"input[name='{name}']")
    return str(field.get("value")) if field and field.get("value") else None


def _extract_parenthesized_type(link: HtmlNode, row_text: str) -> str:
    match = re.search(r"\(([^)]+)\)", link.parent.get_text(" ", strip=True) if link.parent else "")
    value = _normalize_text(match.group(1)) if match else "decisao"
    normalized = value.lower()
    if "acórd" in normalized or "acord" in normalized:
        return "acordao"
    if "monocr" in normalized:
        return "decisao_monocratica"
    if "senten" in normalized:
        return "sentenca"
    return value or "decisao"


def _label_value(text: str, label: str) -> str:
    start = text.find(label)
    if start < 0:
        return ""
    return text[start + len(label) :].strip()


def _truncate_at_labels(value: str | None) -> str | None:
    if not value:
        return None
    for label in ("Processo:", "Órgão Julgador:", "Data Julgamento:", "Segredo de Justiça"):
        value = value.split(label, 1)[0]
    return _normalize_text(value) or None


def _parse_total(text: str) -> int:
    match = re.search(r"([\d.]+)\s+registro\(s\) encontrado", text, re.IGNORECASE)
    return int(match.group(1).replace(".", "")) if match else 0


def _is_explicit_empty(text: str) -> bool:
    normalized = text.lower()
    return "registro(s) encontrado" in normalized or "nenhum resultado" in normalized


def _parse_br_date(value: str) -> str | None:
    match = DATE_PATTERN.search(value or "")
    if not match:
        return None
    return datetime.strptime(match.group(0), "%d/%m/%Y").date().isoformat()


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0) if match else None


def _strip_session_id(url: str) -> str:
    return SESSION_ID_PATTERN.sub("", url)


def _normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _looks_like_access_control(text: str) -> bool:
    normalized = text.lower()
    return any(marker in normalized for marker in ("captcha", "acesso negado", "access denied"))


def _empty_page(query: JurisprudenceQuery, trace: SourceTrace, reason: str) -> SearchPage:
    return SearchPage(
        source="tjpr_jurisprudencia",
        total=0,
        start=0,
        end=0,
        page=query.page,
        page_size=query.page_size,
        results=[],
        source_trace=trace,
        pagination_mode="page",
        is_complete=True,
        completeness_reason=reason,
    )


def _raise_for_tjpr_response(response: Any, operation: str) -> None:
    status = int(getattr(response, "status_code", 0) or 0)
    text = str(getattr(response, "text", "") or "")
    if status in {401, 403} or _looks_like_access_control(text):
        raise AccessControlRequiredError(f"{operation} returned access-control response")
    if status == 429:
        raise RateLimitDetectedError(f"{operation} returned HTTP 429")
    if status >= 500:
        raise SourceUnavailableError(f"{operation} returned HTTP {status}")
    if status >= 400:
        raise SourceUnavailableError(f"{operation} returned HTTP {status}")
