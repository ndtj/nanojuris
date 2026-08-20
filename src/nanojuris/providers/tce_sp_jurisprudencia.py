"""TCE-SP public jurisprudence catalog provider."""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
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


class TceSpJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for public TCE-SP jurisprudence summaries and bulletins."""

    name = "tce_sp_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        selected_types = _selected_types(query.types)
        trace = SourceTrace(
            provider=self.name,
            endpoint="/boletim-de-jurisprudencia/(sumulas|publicacoes)",
            query=query.to_dict(),
            source_url=self.config.tce_sp_url,
            limitations=[
                "Catalogos publicos do TCE-SP validados com sessao HTTP limpa.",
                "A busca dinamica /jurisprudencia/pesquisar contem reCAPTCHA e nao e automatizada.",
            ],
        )
        results: list[JurisprudenceResult] = []
        if "sumula" in selected_types:
            html, source_url = self._request_text("GET", "/boletim-de-jurisprudencia/sumulas")
            results.extend(parse_tce_sp_sumulas(html, source_url=source_url, trace=trace))
        if "boletim" in selected_types:
            html, source_url = self._request_text("GET", "/boletim-de-jurisprudencia/publicacoes")
            results.extend(parse_tce_sp_boletins(html, source_url=source_url, trace=trace))

        normalized_query = _normalize_text(query.text or query.exact_phrase)
        if normalized_query:
            results = [
                result
                for result in results
                if normalized_query
                in _normalize_text(
                    " ".join(
                        str(value or "")
                        for value in [
                            result.summary,
                            result.thesis,
                            result.question,
                            result.raw,
                        ]
                    )
                )
            ]

        start_index = (query.page - 1) * query.page_size
        limited = results[start_index : start_index + query.page_size]
        start = start_index + 1 if limited else 0
        return SearchPage(
            source=self.name,
            total=len(results),
            start=start,
            end=start + len(limited) - 1 if limited else 0,
            page=query.page,
            page_size=query.page_size,
            results=limited,
            source_trace=trace,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[],
            raw={"message": "TCE-SP catalog provider does not expose linked decision text."},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TCE-SP Jurisprudencia",
            source_url=self.config.tce_sp_url.rstrip("/") + "/boletim-de-jurisprudencia",
            category="administrative_jurisprudence",
            search_modes=["text", "catalog", "document_type"],
            document_types=["sumula", "boletim_jurisprudencia"],
            content_formats=["html"],
            canonical_records=["CanonicalPrecedent"],
            extracted_fields=[
                "summary_number",
                "statement",
                "history",
                "foundation",
                "bulletin_edition",
                "bulletin_url",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /boletim-de-jurisprudencia/sumulas",
                "GET /boletim-de-jurisprudencia/publicacoes",
                "GET /boletim-de-jurisprudencia/indice-alfabetico-remissivo",
            ],
            supports_full_text=False,
            pagination_mode="local_window",
            completeness_contract="observed_window_only",
            full_text_access="link_only",
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=["text", "types"],
            limitations=[
                "Provider usa catalogos estaticos; busca dinamica com reCAPTCHA "
                "nao e automatizada.",
                "Boletins sao listados por URL publica; texto integral pode variar por pagina.",
            ],
            responsible_use=[
                "Preservar URL publica e SourceTrace para auditoria.",
                "Nao tentar resolver reCAPTCHA da busca dinamica do TCE-SP.",
            ],
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> tuple[str, str]:
        self._respect_rate_limit()
        url = urljoin(self.config.tce_sp_url.rstrip("/") + "/", path.lstrip("/"))
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
            raise SourceUnavailableError(f"TCE-SP jurisprudence request failed: {exc}") from exc

        response.encoding = response.encoding or response.apparent_encoding or "utf-8"
        if response.status_code == 429:
            raise RateLimitDetectedError("TCE-SP jurisprudence returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(
                f"TCE-SP jurisprudence returned HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TCE-SP jurisprudence rejected request with HTTP {response.status_code}"
            )
        return response.text, getattr(response, "url", url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def parse_tce_sp_sumulas(
    html: str,
    *,
    source_url: str,
    trace: SourceTrace,
) -> list[JurisprudenceResult]:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article")
    if not isinstance(article, Tag):
        raise ParserContractChangedError("TCE-SP sumulas article not found")
    text = _clean_text(article.get_text(" ", strip=True))
    matches = list(re.finditer(r"S[ÚU]MULA\s+N[ºO]\s*(\d+)\s*-\s*", text, flags=re.I))
    if not matches:
        raise ParserContractChangedError("TCE-SP sumulas not found")
    results: list[JurisprudenceResult] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        number = int(match.group(1))
        block = _clean_text(text[start:end])
        statement = _clean_text(block.split("(Veja histórico", 1)[0])
        history = _extract_table_after_heading(article, index)
        result_trace = SourceTrace(
            provider=trace.provider,
            endpoint="/boletim-de-jurisprudencia/sumulas",
            query={"sumula": number},
            source_url=source_url,
            limitations=trace.limitations,
        )
        results.append(
            JurisprudenceResult(
                id=f"tce-sp-sumula-{number}",
                source="tce_sp_jurisprudencia",
                court="TCE-SP",
                type="sumula",
                number=number,
                thesis=statement,
                summary=f"Súmula nº {number} - {statement}",
                source_trace=result_trace,
                raw={"statement": statement, "history": history, "source_url": source_url},
            )
        )
    return results


def parse_tce_sp_boletins(
    html: str,
    *,
    source_url: str,
    trace: SourceTrace,
) -> list[JurisprudenceResult]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[JurisprudenceResult] = []
    seen: set[str] = set()
    for node in soup.find_all("a", href=True):
        title = _clean_text(node.get_text(" ", strip=True))
        if "Boletim" not in title or "Jurisprudência" not in title:
            continue
        url = urljoin(source_url, str(node.get("href") or ""))
        if url in seen:
            continue
        seen.add(url)
        edition = _extract_edition(title)
        result_trace = SourceTrace(
            provider=trace.provider,
            endpoint="/boletim-de-jurisprudencia/publicacoes",
            query={"edition": edition},
            source_url=url,
            limitations=trace.limitations,
        )
        results.append(
            JurisprudenceResult(
                id=f"tce-sp-boletim-{edition or len(results) + 1}",
                source="tce_sp_jurisprudencia",
                court="TCE-SP",
                type="boletim_jurisprudencia",
                number=edition,
                summary=title,
                source_trace=result_trace,
                raw={"title": title, "document_url": url, "source_url": source_url},
            )
        )
    if not results:
        raise ParserContractChangedError("TCE-SP boletim links not found")
    return results


def _selected_types(values: list[str]) -> list[str]:
    selected: list[str] = []
    for value in values:
        normalized = _normalize_text(value).replace(" ", "_")
        if normalized in {"sumula", "boletim", "boletim_jurisprudencia"}:
            selected.append("boletim" if normalized.startswith("boletim") else normalized)
    return selected or ["sumula", "boletim"]


def _extract_table_after_heading(article: Tag, index: int) -> str | None:
    tables = article.find_all("table")
    if index < len(tables):
        return _clean_text(tables[index].get_text(" ", strip=True))
    return None


def _extract_edition(title: str) -> int | None:
    match = re.search(r"(?:N[.ºo]*|Edição\s+N[.ºo]*)\s*(\d+)", title, flags=re.I)
    return int(match.group(1)) if match else None


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_text(value: object) -> str:
    normalized = _clean_text(str(value or "")).casefold()
    replacements = {
        "á": "a",
        "à": "a",
        "â": "a",
        "ã": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for original, replacement in replacements.items():
        normalized = normalized.replace(original, replacement)
    return normalized
