"""STJ Informativo public jurisprudence provider."""

from __future__ import annotations

import re
import time
import unicodedata
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
    DecisionBundle,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider


class StjInformativoProvider(JurisprudenceProvider):
    """Provider for STJ Informativo de Jurisprudencia public HTML."""

    name = "stj_informativo"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/jurisprudencia/externo/informativo/"
        params = {
            "acao": "pesquisar",
            "livre": query.number or query.text,
            "operador": "E",
            "b": "INFJ",
            "tp": "T",
        }
        html = self._request_text(endpoint, params=params)
        source_url = urljoin(self.config.stj_url.rstrip("/") + "/", endpoint.lstrip("/"))
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"GET {endpoint}",
            query={**params, "page": query.page, "page_size": query.page_size},
            source_url=source_url,
            limitations=[
                "HTML publico do Informativo de Jurisprudencia do STJ.",
                "Fonte curada por notas; nao substitui busca integral de acordaos SCON.",
                "Links para acordaos/inteiro teor podem apontar para rotas protegidas.",
            ],
        )
        return parse_stj_informativo_results(
            html,
            query=query,
            trace=trace,
            base_url=self.config.stj_url,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[],
            raw={"message": "stj_informativo exposes public note text and linked case metadata."},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="STJ Informativo",
            source_url="https://processo.stj.jus.br/jurisprudencia/externo/informativo/",
            category="court_jurisprudence",
            search_modes=["text", "case_number", "stj_informativo_query"],
            document_types=["informativo", "nota_jurisprudencia"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "informativo",
                "period",
                "case_number",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "title",
                "summary",
                "document_url",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=["GET /jurisprudencia/externo/informativo/"],
            supports_full_text=False,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=["text", "number"],
            limitations=[
                "Retorna notas curadas do Informativo STJ, nao a base integral SCON.",
                "Acordaos referenciados podem depender de rotas SCON sujeitas a verificacao.",
                "Parser HTML depende de blocos .clsInformativoBlocoItem.",
            ],
            responsible_use=[
                "Usar termos especificos e page_size pequeno.",
                "Nao contornar validacao automatica em links de acordaos.",
                "Preservar a nota oficial e a referencia ao informativo na analise.",
            ],
        )

    def _request_text(self, path: str, **kwargs: Any) -> str:
        self._respect_rate_limit()
        url = urljoin(self.config.stj_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        try:
            response = self.session.get(url, headers=headers, timeout=self.config.timeout, **kwargs)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"STJ Informativo request failed: {exc}") from exc
        response.encoding = response.encoding or "ISO-8859-1"
        text = response.text
        if response.status_code in {401, 403} and _looks_like_access_control(text):
            raise AccessControlRequiredError("STJ Informativo requires access-control validation")
        if response.status_code == 429:
            raise RateLimitDetectedError("STJ Informativo returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"STJ Informativo returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"STJ Informativo rejected request with HTTP {response.status_code}"
            )
        if _looks_like_access_control(text):
            raise AccessControlRequiredError("STJ Informativo requires access-control validation")
        return text

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def parse_stj_informativo_results(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    """Parse STJ Informativo public HTML into normalized results."""

    if _looks_like_access_control(html):
        raise AccessControlRequiredError("STJ Informativo returned access-control HTML")
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".clsInformativoBlocoItem")
    if not items:
        text = soup.get_text(" ", strip=True).lower()
        if "nenhum item encontrado" in text or "notas encontradas: 0" in text:
            return SearchPage(
                source="stj_informativo",
                total=0,
                start=0,
                end=0,
                page=query.page,
                page_size=query.page_size,
                results=[],
                source_trace=trace,
            )
        raise ParserContractChangedError("STJ Informativo result blocks not found")

    results = [
        _item_to_result(item, trace=trace, base_url=base_url, index=index)
        for index, item in enumerate(items, start=1)
    ]
    matches = [item for item in results if _matches_result(item, query)]
    total = _parse_total(soup) or len(matches)
    start_index = max(query.page - 1, 0) * query.page_size
    page_results = matches[start_index : start_index + query.page_size]
    start = start_index + 1 if page_results else 0
    return SearchPage(
        source="stj_informativo",
        total=total if len(matches) == len(results) else len(matches),
        start=start,
        end=start + len(page_results) - 1 if page_results else 0,
        page=query.page,
        page_size=query.page_size,
        results=page_results,
        source_trace=trace,
    )


def _item_to_result(
    item: Any,
    *,
    trace: SourceTrace,
    base_url: str,
    index: int,
) -> JurisprudenceResult:
    text = _normalize_spaces(item.get_text(" ", strip=True))
    title = _extract_title(item, text)
    body = _extract_body(item, title)
    case_number = _extract_case_number(item)
    document_url = _extract_document_url(item, base_url=base_url)
    informativo = _match_group(r"Informativo\s*n[ºo.]?\s*(\d+)", text)
    period = _match_group(r"Per[ií]odo:\s*([^\.]+(?:\d{4})?)", text)
    judging_body = _extract_judging_body(text)
    rapporteur = _match_group(r"Rel\.\s*Min\.\s*([^,]+)", text)
    judgment_date = _match_group(r"julgado em\s*(\d{2}/\d{2}/\d{4})", text)
    source_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
        source_url=document_url or trace.source_url,
        limitations=trace.limitations,
    )
    return JurisprudenceResult(
        id=f"stj-informativo-{informativo or index}-{_slug(case_number or title or str(index))}",
        source="stj_informativo",
        court="STJ",
        type="informativo",
        number=case_number,
        summary=body or title or None,
        rapporteur=rapporteur,
        updated_at=judgment_date,
        source_trace=source_trace,
        raw={
            "informativo": informativo,
            "period": period,
            "orgao_julgador": judging_body,
            "judging_body": judging_body,
            "title": title or None,
            "data_julgamento": judgment_date,
            "judgment_date": judgment_date,
            "document_url": document_url,
            "raw_text": text,
        },
    )


def _extract_title(item: Any, fallback_text: str) -> str:
    title_candidates = item.select(".clsInformativoTextoBlocoTitulo, .clsInformativoTitulo")
    for candidate in title_candidates:
        text = _normalize_spaces(candidate.get_text(" ", strip=True))
        if text and not text.lower().startswith("informativo"):
            return text
    match = re.search(r"(DIREITO\s+.+?\.)\s+Compartilhe:", fallback_text, re.I)
    if match:
        return _normalize_spaces(match.group(1))
    match = re.search(r"(DIREITO\s+[A-ZÁ-Ú\s]+?\.\s*[^\.]+\.)", fallback_text)
    return _normalize_spaces(match.group(1)) if match else ""


def _extract_body(item: Any, title: str) -> str:
    body = item.select_one(".clsInformativoTexto")
    if body:
        return _normalize_spaces(body.get_text(" ", strip=True))
    text = _normalize_spaces(item.get_text(" ", strip=True))
    if title and title in text:
        return _normalize_spaces(text.split(title, 1)[-1])
    return text


def _extract_case_number(item: Any) -> str | None:
    for anchor in item.select("a[href]"):
        text = _normalize_spaces(anchor.get_text(" ", strip=True))
        if re.search(r"\b[A-Z]{1,8}\s+\d", text):
            return text
    text = _normalize_spaces(item.get_text(" ", strip=True))
    match = re.search(r"\b([A-Z]{1,8}\s+\d[\d\.\-]*/?[A-Z]{0,2})\b", text)
    return match.group(1) if match else None


def _extract_document_url(item: Any, *, base_url: str) -> str | None:
    fallback: str | None = None
    for anchor in item.select("a[href]"):
        text = anchor.get_text(" ", strip=True)
        href = str(anchor.get("href") or "")
        if re.search(r"\b[A-Z]{1,8}\s+\d", text):
            return urljoin(base_url.rstrip("/") + "/", href.lstrip("/"))
        if "@CNOT" in href and fallback is None:
            fallback = urljoin(base_url.rstrip("/") + "/", href.lstrip("/"))
    return fallback


def _extract_judging_body(text: str) -> str | None:
    bodies = [
        "CORTE ESPECIAL",
        "PRIMEIRA SEÇÃO",
        "SEGUNDA SEÇÃO",
        "TERCEIRA SEÇÃO",
        "PRIMEIRA TURMA",
        "SEGUNDA TURMA",
        "TERCEIRA TURMA",
        "QUARTA TURMA",
        "QUINTA TURMA",
        "SEXTA TURMA",
        "PLENÁRIO",
    ]
    normalized = text.upper()
    for body in bodies:
        if body in normalized:
            return body.title()
    return None


def _matches_result(result: JurisprudenceResult, query: JurisprudenceQuery) -> bool:
    haystack = _normalize_search(
        " ".join(
            [
                str(result.number or ""),
                result.summary or "",
                result.rapporteur or "",
                " ".join(str(value or "") for value in result.raw.values()),
            ]
        )
    )
    text = _normalize_search(query.text)
    number = _normalize_search(query.number)
    if text and text not in haystack:
        return False
    if number and number not in _normalize_search(str(result.number or "")):
        return False
    return True


def _parse_total(soup: BeautifulSoup) -> int:
    text = _normalize_spaces(soup.get_text(" ", strip=True))
    match = re.search(r"Notas encontradas:\s*(\d+)", text, re.I)
    return int(match.group(1)) if match else 0


def _looks_like_access_control(html: str) -> bool:
    lowered = html.lower()
    if "clsinformativoblocoitem" in lowered or "nenhum item encontrado" in lowered:
        return False
    return (
        "challenge-error-text" in lowered
        or "enable javascript and cookies to continue" in lowered
        or ("captcha" in lowered and "informativo" not in lowered)
    )


def _match_group(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.I)
    return _normalize_spaces(match.group(1)) if match else None


def _normalize_spaces(value: str) -> str:
    without_private_glyphs = re.sub(r"[\ue000-\uf8ff]", " ", value)
    normalized = re.sub(r"\s+", " ", without_private_glyphs).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", normalized)


def _normalize_search(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", _normalize_spaces(value).casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower() or "registro"
