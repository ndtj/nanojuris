"""TRT3 official curated appellate ementario volume.

The TRT3 Digital Library publishes individual ementario volumes as public PDFs.
This adapter searches one observed volume in memory and deliberately exposes it
as a contextual, opt-in collection.  It does not claim to be the TRT3 corpus,
does not infer the existence of a remote search API and never treats a missing
CNJ entry in a valid PDF as an empty response when the parser contract changes.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from io import BytesIO
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import (
    DocumentReference,
    build_canonical_document,
    fetch_document_reference,
)
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
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus

MAX_PDF_BYTES = 8_000_000
MAX_HTML_BYTES = 600_000
MAX_RESULTS = 500
MAX_VOLUMES_PER_QUERY = 3
_HOST = "as1.trt3.jus.br"
_DSpace_HOST = "sistemas.trt3.jus.br"
_COLLECTION_PATH = "/bd-trt3/handle/11103/3797"
_SEARCH_PATH = f"{_COLLECTION_PATH}/advanced-search"
_CASE_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.5\.03\.\d{4}\b")
_TOTAL_RE = re.compile(r"produziu\s+([\d.]+)\s+resultado", re.IGNORECASE)
_MONTHS = {
    "janeiro": "01",
    "fevereiro": "02",
    "marco": "03",
    "março": "03",
    "abril": "04",
    "maio": "05",
    "junho": "06",
    "julho": "07",
    "agosto": "08",
    "setembro": "09",
    "outubro": "10",
    "novembro": "11",
    "dezembro": "12",
}


class Trt3EmentarioJurisprudenciaProvider(JurisprudenceProvider):
    """Search the bounded public TRT3 ementario PDF window."""

    name = "trt3_ementario_jurisprudencia"
    authority = "TRT3"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.trt3_ementario_jurisprudencia_url).hostname or _HOST
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host, _DSpace_HOST),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_PDF_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._observed: dict[str, str] = {}
        self._observed_text: dict[str, str] = {}
        self._observed_documents: dict[str, tuple[str, SourceTrace]] = {}
        self._last_bytes: bytes | None = None
        self._last_trace: SourceTrace | None = None
        self._dspace_transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(_DSpace_HOST,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_HTML_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        volume_items, search_trace, reported_total = self._request_dspace_search(query)
        results: list[JurisprudenceResult] = []
        volume_failures: list[str] = []
        for item in volume_items[:MAX_VOLUMES_PER_QUERY]:
            try:
                content, trace, pdf_url, volume_title = self._request_dspace_volume(item)
                parsed = parse_trt3_ementario_pdf(
                    content,
                    query=query,
                    trace=trace,
                    volume_id=item["handle"],
                    volume_title=volume_title,
                    document_url=pdf_url,
                )
            except (ParserContractChangedError, SourceUnavailableError) as exc:
                volume_failures.append(str(exc))
                continue
            results.extend(parsed)
            for result in parsed:
                self._observed[result.id] = pdf_url
                self._observed_text[result.id] = result.summary or ""
                self._observed_documents[result.id] = (pdf_url, trace)
        # Stable identity across overlapping DSpace volume searches.
        deduped: list[JurisprudenceResult] = []
        seen: set[str] = set()
        for result in results:
            if result.id in seen:
                continue
            seen.add(result.id)
            deduped.append(result)
        results = deduped[:MAX_RESULTS]
        if not results and reported_total == 0:
            completeness = True
            completeness_reason = "A busca oficial informou zero volumes para a consulta."
        else:
            completeness = False
            completeness_reason = (
                "A fonte informou o total de volumes, mas apenas uma janela bounded de "
                f"{MAX_VOLUMES_PER_QUERY} volumes foi materializada como ementas."
            )
            if volume_failures:
                completeness_reason += " Alguns volumes não puderam ser extraídos."
        for result in results:
            self._observed[result.id] = result.document_url or self._observed.get(result.id, "")
        page_results = results[: query.page_size]
        return SearchPage(
            source=self.name,
            total=len(results),
            start=1 if page_results else 0,
            end=len(page_results) if page_results else 0,
            page=query.page,
            page_size=query.page_size,
            results=page_results,
            source_trace=search_trace,
            pagination_mode="remote_volume_search_local_pdf_window",
            is_complete=completeness,
            completeness_reason=completeness_reason,
            ordering="source_pdf_order",
            filters_applied={
                "text": "local_postfilter",
                "exact_phrase": "local_postfilter",
                "number": "local_postfilter",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
            },
            # The remote total counts volumes, while this page counts parsed
            # ementas; exposing it as the decision total would be misleading.
            total_known=False,
            access_status=AccessStatus.PUBLIC,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        if precedent_id not in self._observed:
            raise SourceUnavailableError("TRT3 documento exige resultado observado na sessao")
        # Search already loaded the static volume.  Reusing the observed
        # record avoids a second network request and preserves the provider's
        # one-request bounded contract for a user action.
        text = self._observed_text.get(precedent_id, "")
        if not text and self._last_bytes:
            text = _extract_pdf_text(self._last_bytes)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": text, "content_type": "text/plain"}] if text else [],
            source_trace=self._last_trace,
            raw={"collection": "TRT3_EMENTARIO", "document_type": "ementario"},
        )

    def get_document(self, document_id: str):
        if document_id not in self._observed:
            raise SourceUnavailableError("TRT3 documento exige identificador observado")
        observed_document = self._observed_documents.get(document_id)
        if observed_document is not None:
            document_url, trace = observed_document
            return fetch_document_reference(
                DocumentReference(
                    id=document_id,
                    source=self.name,
                    url=document_url,
                    document_type="ementario",
                    expected_content_types=("application/pdf", "application/octet-stream"),
                    decision_id=document_id,
                ),
                policy=self._dspace_transport.policy,
                session=self.session,
                title="TRT3 Ementario de Jurisprudencia",
            )
        if self._last_bytes is not None and self._last_trace is not None:
            return build_canonical_document(
                document_id=document_id,
                source=self.name,
                document_type="ementario",
                content=self._last_bytes,
                content_type="application/pdf",
                url=self.config.trt3_ementario_jurisprudencia_url,
                title="TRT3 Ementario de Jurisprudencia n. 12",
                source_trace=self._last_trace,
                access_status=AccessStatus.PUBLIC,
                raw_metadata={"collection": "TRT3_EMENTARIO", "curated": True},
                parser=f"{self.name}.pdf",
                parser_version="1",
                max_bytes=MAX_PDF_BYTES,
            )
        return fetch_document_reference(
            DocumentReference(
                id=document_id,
                source=self.name,
                url=self.config.trt3_ementario_jurisprudencia_url,
                document_type="ementario",
                expected_content_types=("application/pdf",),
                decision_id=document_id,
            ),
            policy=self.transport.policy,
            session=self.session,
            title="TRT3 Ementario de Jurisprudencia n. 12",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        unsupported = [
            "courts",
            "types",
            "all_words",
            "any_words",
            "without_words",
            "case_class",
            "judging_body",
            "rapporteur",
            "updated_from",
            "updated_to",
            "published_from",
            "published_to",
            "judgment_date_from",
            "judgment_date_to",
            "document_type",
            "decision_type",
            "fetch_details",
            "lawyer_name",
            "legal_area",
            "oab",
            "party_document",
            "party_name",
            "police_document",
            "precatory_number",
            "cda",
            "source_origin",
            "source_origins",
        ]
        return ProviderCapabilities(
            source=self.name,
            display_name="TRT3 Ementario de Jurisprudencia (volume curado)",
            source_url=self.config.trt3_ementario_jurisprudencia_url,
            category="curated_jurisprudence",
            search_modes=["text", "exact_phrase", "case_number", "pagination"],
            document_types=["ementario", "acordao_ementa"],
            content_formats=["pdf", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator="authority=TRT3;branch=labor;degree=second;collection=TRT3_EMENTARIO",
            extracted_fields=[
                "case_number",
                "summary",
                "full_text",
                "document_url",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=["GET official TRT3 ementario PDF"],
            supports_full_text=False,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            pagination_mode="remote_volume_search_local_pdf_window",
            max_remote_page_size=100,
            completeness_contract="static_volume_total_known_not_corpus_complete",
            full_text_access="document_link",
            supported_filters=["text", "exact_phrase", "number", "page"],
            unsupported_filters=unsupported,
            filter_semantics={
                "text": "local_postfilter",
                "exact_phrase": "local_postfilter",
                "number": "local_postfilter",
                "page": "remote_volume_window",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                **{name: "unsupported" for name in unsupported},
            },
            ordering_modes=["source_pdf_order"],
            detail_modes=["volume_pdf"],
            limitations=[
                (
                    "A busca remota retorna volumes editoriais; nao e busca geral nem "
                    "acervo integral do TRT3."
                ),
                "Apenas tres volumes por consulta sao materializados para manter a sonda bounded.",
                "O PDF contem ementas; inteiro teor dos votos nao foi demonstrado.",
            ],
            responsible_use=["Usar consultas bounded e preservar o escopo curado."],
        )

    def _request_dspace_search(
        self, query: JurisprudenceQuery
    ) -> tuple[list[dict[str, str]], SourceTrace, int | None]:
        terms = query.exact_phrase.strip() or query.text.strip() or query.number.strip()
        data = {
            "results_per_page": str(min(max(query.page_size, 1), 5)),
            "query1": terms,
            "field1": "ANY",
            "conjunction1": "AND",
            "num_search_field": "5",
            "rpp": str(min(max(query.page_size, 1), 5)),
            "sort_by": "0",
            "order": "DESC",
            "page": str(max(query.page, 1)),
            "submit": "Buscar",
        }
        request = TransportRequest(
            source=self.name,
            operation="dspace_advanced_search",
            method="POST",
            url=f"https://{_DSpace_HOST}{_SEARCH_PATH}",
            data=data,
            headers={"Accept": "text/html,application/xhtml+xml"},
            idempotent=False,
        )
        response = self._dspace_transport.request(request)
        _ensure_response(response, "TRT3 DSpace advanced search")
        items, reported_total = _parse_dspace_search_html(
            response.text, source_base=f"https://{_DSpace_HOST}"
        )
        trace = SourceTrace(
            provider=self.name,
            endpoint="POST /bd-trt3/handle/11103/3797/advanced-search",
            query={"text": query.text, "exact_phrase": query.exact_phrase, "page": query.page},
            source_url=f"https://{_DSpace_HOST}{_SEARCH_PATH}",
            final_url=response.final_url,
            http_status=response.status_code,
            content_type=response.content_type,
            content_sha256=response.content_sha256,
            response_bytes=response.byte_size,
            elapsed_ms=response.elapsed_ms,
            retrieval_status="ok",
            transformations=["dspace_html_search_parsed"],
            limitations=[
                "O total remoto corresponde a volumes do ementario, nao a decisoes individuais.",
                f"Apenas {MAX_VOLUMES_PER_QUERY} volumes sao abertos nesta chamada.",
            ],
        )
        return items, trace, reported_total

    def _request_dspace_volume(self, item: dict[str, str]) -> tuple[bytes, SourceTrace, str, str]:
        page_request = TransportRequest(
            source=self.name,
            operation="dspace_volume_page",
            method="GET",
            url=item["handle"],
            headers={"Accept": "text/html,application/xhtml+xml"},
            idempotent=True,
        )
        page_response = self._dspace_transport.request(page_request)
        _ensure_response(page_response, "TRT3 DSpace volume page")
        soup = BeautifulSoup(page_response.text, "html.parser")
        pdf_link = next(
            (
                str(anchor.get("href"))
                for anchor in soup.select('a[href*="/bitstream/"]')
                if ".pdf" in str(anchor.get("href", "")).casefold()
            ),
            None,
        )
        if not pdf_link:
            raise ParserContractChangedError("TRT3 volume did not expose a PDF bitstream")
        pdf_url = urljoin(item["handle"], pdf_link)
        pdf_request = TransportRequest(
            source=self.name,
            operation="dspace_volume_pdf",
            method="GET",
            url=pdf_url,
            headers={"Accept": "application/pdf"},
            idempotent=True,
        )
        pdf_response = self.transport.request(pdf_request)
        _ensure_response(pdf_response, "TRT3 DSpace volume PDF")
        body = bytes(pdf_response.body)
        if not body.startswith(b"%PDF"):
            raise ParserContractChangedError("TRT3 volume did not return a PDF")
        raw_title = soup.title.get_text(" ", strip=True) if soup.title else item["title"]
        title = " ".join(raw_title.split())
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET official TRT3 DSpace ementario PDF",
            query={"volume": item["handle"]},
            source_url=pdf_url,
            final_url=pdf_response.final_url,
            http_status=pdf_response.status_code,
            content_type=pdf_response.content_type,
            content_sha256=pdf_response.content_sha256,
            response_bytes=pdf_response.byte_size,
            elapsed_ms=pdf_response.elapsed_ms,
            retrieval_status="ok",
            transformations=["dspace_item_page_parsed", "pdf_bitstream_extracted"],
            limitations=["O PDF e um volume curado de ementas; nao e inteiro teor dos votos."],
        )
        return body, trace, pdf_url, title

    def _request_volume(self, query: JurisprudenceQuery) -> tuple[bytes, SourceTrace]:
        request = TransportRequest(
            source=self.name,
            operation="volume_fetch",
            method="GET",
            url=self.config.trt3_ementario_jurisprudencia_url,
            headers={"Accept": "application/pdf"},
            idempotent=True,
        )
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TRT3 ementario request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            if response.status is TransportStatus.TIMEOUT:
                raise SourceUnavailableError("TRT3 ementario request timeout")
            raise SourceUnavailableError(
                f"TRT3 ementario transport failed: {response.error_type or response.status.value}"
            )
        status = response.status_code or 0
        if status == 429:
            raise RateLimitDetectedError("TRT3 ementario returned HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TRT3 ementario returned HTTP {status}")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TRT3 ementario returned HTTP {status}")
        body = bytes(response.body)
        if not body.startswith(b"%PDF"):
            raise ParserContractChangedError("TRT3 ementario did not return a PDF")
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET official TRT3 ementario PDF",
            query={"text": query.text, "number": query.number, "page": query.page},
            source_url=response.final_url or self.config.trt3_ementario_jurisprudencia_url,
            final_url=response.final_url,
            http_status=status,
            content_type=response.content_type,
            content_sha256=response.content_sha256,
            response_bytes=response.byte_size,
            elapsed_ms=response.elapsed_ms,
            retrieval_status="ok",
            limitations=[
                "Volume estatico e curado; total conhecido refere-se apenas ao volume observado.",
                "Nao ha pagina remota nem total do acervo TRT3.",
            ],
        )
        self._last_bytes = body
        self._last_trace = trace
        return body, trace


def parse_trt3_ementario_pdf(
    content: bytes,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    volume_id: str = "volume-12",
    volume_title: str = "TRT3 Ementario de Jurisprudencia n. 12",
    document_url: str | None = None,
    publication_date: str | None = None,
) -> list[JurisprudenceResult]:
    if not content.startswith(b"%PDF"):
        raise ParserContractChangedError("TRT3 ementario nao e PDF")
    try:
        text = _extract_pdf_text(content)
    except Exception as exc:  # pypdf raises several parser-specific exceptions
        raise ParserContractChangedError("TRT3 ementario PDF nao pode ser extraido") from exc
    blocks = _record_blocks(text)
    if not blocks and text.strip():
        raise ParserContractChangedError("TRT3 ementario nao expos identificadores de processos")
    results: list[JurisprudenceResult] = []
    for index, (number, block) in enumerate(blocks[:MAX_RESULTS], start=1):
        if not _matches(block, number, query):
            continue
        digest = hashlib.sha1(f"{volume_id}:{number}:{index}".encode()).hexdigest()[:12]
        results.append(
            JurisprudenceResult(
                id=f"trt3-ementario-{digest}",
                source="trt3_ementario_jurisprudencia",
                court="TRT3",
                type="ementario",
                number=number,
                summary=block,
                full_text=None,
                judgment_date=None,
                publication_date=publication_date or _volume_publication_date(volume_title),
                degree="second",
                instance="second",
                branch="labor",
                authority="TRT3",
                collection="TRT3_EMENTARIO",
                document_type="ementario",
                document_url=document_url or trace.source_url,
                access_status=AccessStatus.PUBLIC,
                source_trace=trace,
                raw={
                    "source_record_id": f"trt3-{volume_id}-{index}",
                    "volume_title": volume_title,
                    "curated": True,
                },
                field_provenance={
                    "number": {"source": "pdf_text", "confidence": "observed"},
                    "summary": {"source": "pdf_text", "confidence": "observed"},
                    "degree": {"source": "official_collection_scope", "confidence": "validated"},
                },
            )
        )
    return results


def _ensure_response(response: Any, label: str) -> None:
    """Map transport outcomes without ever turning them into an empty page."""

    if response.status is not TransportStatus.COMPLETE:
        raise SourceUnavailableError(
            f"{label} transport failed: {response.error_type or response.status.value}"
        )
    status = int(response.status_code or 0)
    if status == 429:
        raise RateLimitDetectedError(f"{label} returned HTTP 429")
    if status in {401, 403, 407, 451}:
        raise AccessControlRequiredError(f"{label} returned HTTP {status}")
    if status < 200 or status >= 300:
        raise SourceUnavailableError(f"{label} returned HTTP {status}")


def _parse_dspace_search_html(
    content: str, *, source_base: str
) -> tuple[list[dict[str, str]], int | None]:
    """Parse DSpace's stable result list without treating malformed HTML as empty."""

    soup = BeautifulSoup(content, "html.parser")
    result_list = soup.select("li.ds-artifact-item")
    if not result_list and "result-query" not in content:
        raise ParserContractChangedError("TRT3 DSpace search result list is missing")
    items: list[dict[str, str]] = []
    for node in result_list:
        link = node.select_one(".artifact-title a[href]")
        if link is None:
            continue
        href = str(link.get("href") or "")
        if "/handle/11103/" not in href:
            continue
        items.append(
            {
                "handle": urljoin(source_base, href),
                "title": " ".join(link.get_text(" ", strip=True).split()),
            }
        )
    result_node = soup.select_one(".result-query")
    result_text = " ".join((result_node or soup).get_text(" ", strip=True).split())
    total_match = _TOTAL_RE.search(_normalize(result_text))
    total = int(total_match.group(1).replace(".", "")) if total_match else None
    return items, total


def _extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _record_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(_CASE_RE.finditer(text))
    return [
        (
            match.group(0),
            _clean(text[match.start() : matches[i + 1].start() if i + 1 < len(matches) else None]),
        )
        for i, match in enumerate(matches)
    ]


def _matches(block: str, number: str, query: JurisprudenceQuery) -> bool:
    normalized = _normalize(block)
    if query.number and _normalize(query.number) not in _normalize(number):
        return False
    phrase = query.exact_phrase.strip()
    if phrase and _normalize(phrase) not in normalized:
        return False
    terms = [part for part in (query.text or "").split() if part]
    if terms and not all(_normalize(term) in normalized for term in terms):
        return False
    excluded = [part for part in query.without_words.split() if part]
    return not any(_normalize(term) in normalized for term in excluded)


def _clean(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split()).strip()


def _normalize(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    )


def _volume_publication_date(title: str) -> str | None:
    """Return an ISO month when the official volume title exposes one."""

    normalized = _normalize(title)
    year_match = re.search(r"\b(19|20)\d{2}\b", normalized)
    if year_match is None:
        return None
    for month, number in _MONTHS.items():
        if _normalize(month) in normalized:
            return f"{year_match.group(0)}-{number}"
    return year_match.group(0)


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.exact_phrase.strip(), query.number.strip())):
        raise QueryRejectedError("TRT3 ementario exige texto, frase ou numero")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TRT3 ementario suporta somente segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TRT3 ementario suporta somente segunda instancia")
    if query.branch and query.branch.casefold() not in {"labor", "trabalhista"}:
        raise QueryRejectedError("TRT3 pertence ao ramo trabalhista")
    if query.authority and query.authority.casefold() not in {"trt3", "trt-3"}:
        raise QueryRejectedError("a autoridade solicitada nao corresponde ao TRT3")


__all__ = ["Trt3EmentarioJurisprudenciaProvider", "parse_trt3_ementario_pdf"]
