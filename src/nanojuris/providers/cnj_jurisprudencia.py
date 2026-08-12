"""CNJ public jurisprudence informativos provider."""

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


class CnjJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for CNJ's curated Informativos de Jurisprudencia catalog."""

    name = "cnj_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/jurisprudencia"
        params = _query_params(query)
        html, final_url = self._request_text(endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /jurisprudencia",
            query=params,
            source_url=final_url,
            limitations=[
                "Catalogo curado de Informativos de Jurisprudencia do CNJ; "
                "nao representa a busca integral de acordaos.",
                "A ementa/resumo e editorial; o PDF oficial permanece como fonte primaria.",
                "O PDF nao e baixado durante a busca.",
            ],
        )
        return parse_cnj_results(
            html,
            query=query,
            trace=trace,
            base_url=self.config.cnj_jurisprudencia_url,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[],
            raw={
                "message": "CNJ Informativos expose curated summaries and official PDF links; "
                "use get_document with the PDF URL for the full source document."
            },
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        if not document_id.startswith(("http://", "https://")):
            raise ValueError("CNJ document_id must be the official PDF URL from raw.document_url")
        content, final_url, content_type = self._request_bytes(document_id)
        digest = hashlib.sha256(content).hexdigest()
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /files/<official-pdf>",
            source_url=final_url,
            content_type=content_type,
            content_sha256=digest,
            response_bytes=len(content),
            limitations=["Documento baixado sob demanda da URL oficial do CNJ."],
        )
        return CanonicalDocument(
            id=document_id,
            source=self.name,
            document_type="informativo_jurisprudencia",
            content_type=content_type,
            url=final_url,
            sha256=digest,
            byte_size=len(content),
            retrieved_at=trace.retrieved_at,
            access_status=AccessStatus.PUBLIC,
            source_trace=trace,
            extraction_trace=ExtractionTrace(
                parser="cnj_jurisprudencia.pdf_bytes",
                parser_version="1",
                status=ExtractionStatus.COMPLETE,
                access_status=AccessStatus.PUBLIC,
                content_sha256=digest,
                content_bytes=len(content),
                metadata={"content_type": content_type},
            ),
            raw_metadata={"content_type": content_type, "bytes_available": True},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="CNJ Informativos de Jurisprudencia",
            source_url=self.config.cnj_jurisprudencia_url.rstrip("/") + "/jurisprudencia",
            category="curated_jurisprudence",
            search_modes=["text", "edition_number", "publication_date", "curated_catalog"],
            document_types=["informativo_jurisprudencia"],
            content_formats=["html", "pdf"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "edition_number",
                "publication_date",
                "summary",
                "document_url",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /jurisprudencia",
                "GET /files/<official-pdf>",
            ],
            # The official PDF is preserved, but its text is not parsed into
            # CanonicalDocument.text by this provider.
            supports_full_text=False,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_suggestions=False,
            supports_live_tests=True,
            pagination_mode="page",
            completeness_contract="reported_html_page_only",
            supported_filters=[
                "text",
                "number",
                "published_from",
                "published_to",
                "page",
            ],
            limitations=[
                "O filtro textual usa o parametro publico argumento.",
                "O PDF e retornado como documento binario sob demanda; a busca nao extrai PDF.",
                "Informativo curado nao deve ser apresentado como acordao individual "
                "ou tese vinculante.",
            ],
            responsible_use=[
                "Citar a edicao, a data e a URL oficial do PDF.",
                "Baixar documentos somente sob demanda, com limite e rate limit.",
                "Preservar a diferenca entre resumo editorial e texto integral.",
            ],
        )

    def _request_text(self, path: str, **kwargs: Any) -> tuple[str, str]:
        response = self._request("GET", path, **kwargs)
        response.encoding = response.encoding or response.apparent_encoding or "utf-8"
        return response.text, str(getattr(response, "url", "") or "")

    def _request_bytes(self, url: str) -> tuple[bytes, str, str]:
        response = self._request("GET", url)
        content = bytes(getattr(response, "content", b""))
        content_type = str(response.headers.get("content-type", "application/octet-stream"))
        if not content.startswith(b"%PDF") and "application/pdf" not in content_type.lower():
            raise ParserContractChangedError("CNJ document URL did not return a PDF payload")
        return content, str(getattr(response, "url", url) or url), content_type

    def _request(self, method: str, url_or_path: str, **kwargs: Any) -> Any:
        self._respect_rate_limit()
        url = (
            url_or_path
            if url_or_path.startswith("http")
            else urljoin(
                self.config.cnj_jurisprudencia_url.rstrip("/") + "/", url_or_path.lstrip("/")
            )
        )
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"CNJ request failed: {exc}") from exc
        status = int(getattr(response, "status_code", 0) or 0)
        text = str(getattr(response, "text", "") or "")
        if status in {401, 403} or _looks_like_access_control(text):
            raise AccessControlRequiredError(f"CNJ returned access-control response: HTTP {status}")
        if status == 429:
            raise RateLimitDetectedError("CNJ returned HTTP 429")
        if status >= 500:
            raise SourceUnavailableError(f"CNJ returned HTTP {status}")
        if status >= 400:
            raise SourceUnavailableError(f"CNJ returned HTTP {status}")
        self._last_request = time.monotonic()
        return response

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)


def parse_cnj_results(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    """Parse the CNJ public informativos table."""

    soup = BeautifulSoup(html, "html.parser")
    table = _find_results_table(soup)
    if table is None:
        text = _normalize_text(soup.get_text(" ", strip=True))
        if "nenhum" in text.lower() or "sem resultado" in text.lower():
            return _empty_page(query, trace, "A fonte informou resultado vazio.")
        raise ParserContractChangedError("CNJ jurisprudence table not found")
    rows = []
    for row in table.select("tbody tr"):
        cells = row.select("td")
        if len(cells) < 4:
            continue
        link = row.select_one("a[href]")
        if link is None:
            continue
        pdf_url = urljoin(base_url.rstrip("/") + "/", str(link["href"]))
        rows.append(
            _row_to_result(
                cells,
                pdf_url=pdf_url,
                trace=trace,
            )
        )
    if not rows:
        return _empty_page(query, trace, "A tabela do CNJ nao possui linhas na pagina.")
    start_index = (query.page - 1) * query.page_size
    page_results = rows[start_index : start_index + query.page_size]
    start = start_index + 1 if page_results else 0
    complete, reason = page_completeness(
        reported_total=len(rows),
        start=start,
        returned=len(page_results),
        total_is_authoritative=False,
    )
    return SearchPage(
        source="cnj_jurisprudencia",
        total=len(rows),
        start=start,
        end=start + len(page_results) - 1 if page_results else 0,
        page=query.page,
        page_size=query.page_size,
        results=page_results,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=reason,
    )


def _row_to_result(cells: list[Tag], *, pdf_url: str, trace: SourceTrace) -> JurisprudenceResult:
    values = [_normalize_text(cell.get_text(" ", strip=True)) for cell in cells[:4]]
    decision_type, number, published_raw, summary = values
    published_date = _parse_br_date(published_raw)
    stable = hashlib.sha256(f"{number}|{published_raw}|{pdf_url}".encode()).hexdigest()[:20]
    result_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
        source_url=pdf_url,
        limitations=trace.limitations,
    )
    return JurisprudenceResult(
        id=f"cnj-informativo-{stable}",
        source="cnj_jurisprudencia",
        court="CNJ",
        type="informativo",
        number=number or None,
        summary=summary or None,
        publication_date=published_date,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=result_trace,
        raw={
            "edition_number": number,
            "type": decision_type,
            "publication_date": published_date,
            "publication_date_raw": published_raw,
            "summary": summary,
            "document_url": pdf_url,
            "curated_source": True,
        },
    )


def _find_results_table(soup: BeautifulSoup) -> Tag | None:
    for table in soup.select("table"):
        headers = [
            _normalize_text(cell.get_text(" ", strip=True)).lower()
            for cell in table.select("thead th")
        ]
        if {"tipo", "número", "data", "ementa"}.issubset(headers):
            return table
    return None


def _query_params(query: JurisprudenceQuery) -> dict[str, str | int]:
    params: dict[str, str | int] = {"page": query.page}
    if query.number:
        params["numero"] = query.number
    if query.text or query.exact_phrase:
        params["argumento"] = query.text or query.exact_phrase
    if query.published_from or query.updated_from:
        params["dat_publicacao_inicio"] = query.published_from or query.updated_from
    if query.published_to or query.updated_to:
        params["dat_publicacao_fim"] = query.published_to or query.updated_to
    return params


def _parse_br_date(value: str) -> str | None:
    match = re.search(r"\d{2}/\d{2}/\d{4}", value or "")
    if not match:
        return None
    return datetime.strptime(match.group(0), "%d/%m/%Y").date().isoformat()


def _normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _looks_like_access_control(text: str) -> bool:
    normalized = text.lower()
    return any(marker in normalized for marker in ("captcha", "acesso negado", "access denied"))


def _empty_page(query: JurisprudenceQuery, trace: SourceTrace, reason: str) -> SearchPage:
    return SearchPage(
        source="cnj_jurisprudencia",
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
