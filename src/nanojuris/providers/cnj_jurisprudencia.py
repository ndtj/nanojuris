"""CNJ public jurisprudence informativos provider."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import DocumentReference, fetch_document_reference
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
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import (
    SharedHttpClient,
    TransportPolicy,
    TransportRequest,
    TransportResponse,
    TransportStatus,
)


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
        self._last_http_metadata: dict[str, Any] = {}
        host = urlparse(self.config.cnj_jurisprudencia_url).hostname or ""
        self._transport_policy = TransportPolicy(
            allowed_hosts=(host, "atos.cnj.jus.br"),
            timeout_seconds=self.config.timeout,
            max_bytes=16_000_000,
            # Preserve the catalog provider's bounded one-shot semantics: a
            # challenge/rate limit must be surfaced, not retried into a
            # second request that could be mistaken for a fresh result.
            max_retries=0,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self._transport = SharedHttpClient(self._transport_policy, session=self.session)
        self._document_policy = TransportPolicy(
            allowed_hosts=(host, "atos.cnj.jus.br"),
            timeout_seconds=self.config.timeout,
            max_retries=2,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self._document_urls: dict[str, str] = {}

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
            **self._last_http_metadata,
        )
        page = parse_cnj_results(
            html,
            query=query,
            trace=trace,
            base_url=self.config.cnj_jurisprudencia_url,
        )
        for result in page.results:
            document_url = result.document_url or result.raw.get("document_url")
            if isinstance(document_url, str) and document_url:
                self._document_urls[result.id] = document_url
        return page

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
        document_url = (
            document_id
            if document_id.startswith("https://")
            else self._document_urls.get(document_id)
        )
        if not document_url:
            raise ValueError(
                "CNJ document_id must be an observed official HTTPS PDF URL or a result id"
            )
        reference = DocumentReference(
            id=document_id,
            source=self.name,
            url=document_url,
            expected_content_types=("application/pdf",),
        )
        return fetch_document_reference(
            reference,
            policy=self._document_policy,
            session=self.session,
            title=f"CNJ Informativo de Jurisprudência {document_id.rsplit('/', 1)[-1]}",
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
            # The official PDF is fetched explicitly and parsed by the shared
            # bounded document pipeline; search still returns only summaries.
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_suggestions=False,
            supports_live_tests=True,
            pagination_mode="page",
            completeness_contract="reported_html_page_only",
            full_text_access="document_link",
            supported_filters=[
                "text",
                "number",
                "published_from",
                "published_to",
                "page",
            ],
            filter_semantics={
                "text": "translated",
                "exact_phrase": "translated",
                "number": "translated",
                "published_from": "translated",
                "published_to": "translated",
                "updated_from": "translated",
                "updated_to": "translated",
                "page": "native",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                **{
                    name: "unsupported"
                    for name in (
                        "courts",
                        "all_words",
                        "any_words",
                        "without_words",
                        "rapporteur",
                        "case_class",
                        "judging_body",
                        "degree",
                        "instance",
                        "legal_area",
                        "decision_type",
                        "judgment_date_from",
                        "judgment_date_to",
                        "types",
                        "source_origin",
                        "source_origins",
                        "fetch_details",
                        "party_name",
                        "party_document",
                        "lawyer_name",
                        "oab",
                        "precatory_number",
                        "police_document",
                        "cda",
                    )
                },
            },
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
        return response.text, response.final_url or response.url

    def _request_bytes(self, url: str) -> tuple[bytes, str, str]:
        response = self._request("GET", url)
        content = response.body
        content_type = str(response.content_type or "application/octet-stream")
        if not content.startswith(b"%PDF") and "application/pdf" not in content_type.lower():
            raise ParserContractChangedError("CNJ document URL did not return a PDF payload")
        return content, response.final_url or response.url or url, content_type

    def _request(self, method: str, url_or_path: str, **kwargs: Any) -> TransportResponse:
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
        params = kwargs.pop("params", {}) or {}
        try:
            response = self._transport.request(
                TransportRequest(
                    source=self.name,
                    operation="search" if method.upper() == "GET" else "request",
                    method=method,
                    url=url,
                    params=params,
                    data=kwargs.pop("data", None),
                    json_body=kwargs.pop("json", None),
                    headers=headers,
                )
            )
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(f"CNJ request failed: {exc}") from exc
        status = int(response.status_code or 0)
        text = response.text
        self._last_http_metadata = {
            "http_status": status,
            "final_url": response.final_url or url,
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok"
            if response.status is TransportStatus.COMPLETE and status < 400
            else response.status.value,
        }
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(f"CNJ request failed: {response.status.value}")
        if status in {401, 403} or _looks_like_access_control(text):
            raise AccessControlRequiredError(f"CNJ returned access-control response: HTTP {status}")
        if status == 429:
            raise RateLimitDetectedError("CNJ returned HTTP 429")
        if status >= 500:
            raise SourceUnavailableError(f"CNJ returned HTTP {status}")
        if status >= 400:
            raise SourceUnavailableError(f"CNJ returned HTTP {status}")
        return response


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
    required_tokens = _query_tokens(query.text or query.exact_phrase or "")
    rows = []
    filtered_out = 0
    for row in table.select("tbody tr"):
        cells = row.select("td")
        if len(cells) < 4:
            continue
        link = row.select_one("a[href]")
        if link is None:
            continue
        row_text = _fold(row.get_text(" ", strip=True))
        if required_tokens and not all(token in row_text for token in required_tokens):
            filtered_out += 1
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
        reason = (
            "Nenhum informativo do CNJ contem todos os termos da consulta."
            if filtered_out
            else "A tabela do CNJ nao possui linhas na pagina."
        )
        return _empty_page(query, trace, reason)
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


_STOPWORDS = {
    "a",
    "as",
    "o",
    "os",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "e",
    "em",
    "no",
    "na",
    "por",
    "com",
    "para",
    "que",
}


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _query_tokens(text: str) -> list[str]:
    return [tok for tok in re.findall(r"[0-9a-z]+", _fold(text)) if tok not in _STOPWORDS]


def _query_params(query: JurisprudenceQuery) -> dict[str, str | int]:
    params: dict[str, str | int] = {"page": query.page}
    if query.number:
        params["numero"] = query.number
    raw_text = query.text or query.exact_phrase
    if raw_text:
        # The CNJ ``argumento`` filter matches the phrase literally, so a
        # multi-word query returns nothing. Send the single most selective
        # token and apply the remaining tokens as a client-side AND filter.
        tokens = _query_tokens(raw_text)
        if tokens:
            params["argumento"] = max(tokens, key=len)
        else:
            params["argumento"] = raw_text
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
