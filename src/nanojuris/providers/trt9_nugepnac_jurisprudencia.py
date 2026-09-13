"""TRT9 official NUGEP/NUGEPNAC curated appellate collections.

The TRT9 jurisprudence bank exposes public PDF compilations for qualified
precedents (IRDR and related incidents).  This adapter deliberately models the
compilation as an opt-in contextual source: it is useful for precedent
discovery, but it is not the tribunal's general Falcao/PJe corpus and must not
be counted as complete TRT9 coverage.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from io import BytesIO
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
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
    ExtractionStatus,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus

MAX_PDF_BYTES = 8_000_000
MAX_RESULTS = 500
_CASE_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.5\.09\.\d{4}\b")
_HOST = "www.trt9.jus.br"


class Trt9NugepnacJurisprudenciaProvider(JurisprudenceProvider):
    """Search an official, bounded TRT9 NUGEP PDF compilation locally."""

    name = "trt9_nugepnac_jurisprudencia"
    authority = "TRT9"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlsplit(self.config.trt9_nugepnac_jurisprudencia_url).hostname or _HOST
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
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
        self._last_bytes: bytes | None = None
        self._last_trace: SourceTrace | None = None

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        collection, url = _collection_url(self.config.trt9_nugepnac_jurisprudencia_url, query)
        content, trace = self._request_pdf(query, url)
        results = parse_trt9_nugepnac_pdf(content, query=query, trace=trace, collection=collection)
        for result in results:
            self._observed[result.id] = url
            self._observed_text[result.id] = result.summary or ""
        start = (query.page - 1) * query.page_size
        page_results = results[start : start + query.page_size]
        return SearchPage(
            source=self.name,
            total=len(results),
            start=start + 1 if page_results else 0,
            end=start + len(page_results) if page_results else 0,
            page=query.page,
            page_size=query.page_size,
            results=page_results,
            source_trace=trace,
            pagination_mode="local_pdf_window",
            is_complete=True,
            completeness_reason=(
                "Compilacao oficial curada carregada integralmente; o total nao representa "
                "o corpus geral do TRT9."
            ),
            ordering="source_pdf_order",
            filters_applied={
                "text": "local_postfilter",
                "exact_phrase": "local_postfilter",
                "number": "local_postfilter",
                "collection": "route_selection",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
            },
            total_known=True,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        if precedent_id not in self._observed:
            raise SourceUnavailableError("TRT9 documento exige resultado observado na sessao")
        text = self._observed_text.get(precedent_id, "")
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": text, "content_type": "text/plain"}] if text else [],
            source_trace=self._last_trace,
            raw={"collection": "TRT9_NUGEP", "document_type": "precedente_qualificado"},
        )

    def get_document(self, document_id: str):
        if document_id not in self._observed:
            raise SourceUnavailableError("TRT9 documento exige identificador observado")
        url = self._observed[document_id]
        if self._last_bytes is not None and self._last_trace is not None:
            return build_canonical_document(
                document_id=document_id,
                source=self.name,
                document_type="precedente_qualificado",
                content=self._last_bytes,
                content_type="application/pdf",
                url=url,
                title="TRT9 NUGEP compilacao de jurisprudencia",
                source_trace=self._last_trace,
                access_status=AccessStatus.PUBLIC,
                raw_metadata={"collection": "TRT9_NUGEP", "curated": True},
                parser=f"{self.name}.pdf",
                parser_version="1",
                max_bytes=MAX_PDF_BYTES,
            )
        return fetch_document_reference(
            DocumentReference(
                id=document_id,
                source=self.name,
                url=url,
                document_type="precedente_qualificado",
                expected_content_types=("application/pdf",),
                decision_id=document_id,
            ),
            policy=self.transport.policy,
            session=self.session,
            title="TRT9 NUGEP compilacao de jurisprudencia",
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
            display_name="TRT9 NUGEP/NUGEPNAC (compilacao curada)",
            source_url=self.config.trt9_nugepnac_jurisprudencia_url,
            category="curated_jurisprudence",
            search_modes=["text", "exact_phrase", "case_number", "pagination"],
            document_types=["precedente_qualificado", "ementa"],
            content_formats=["pdf", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator="authority=TRT9;branch=labor;degree=second;collection=TRT9_NUGEP",
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
            endpoints=["GET official TRT9 NUGEP jurisprudence PDF"],
            supports_full_text=False,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            pagination_mode="local_pdf_window",
            max_remote_page_size=100,
            completeness_contract="static_curated_pdf_total_known_not_corpus_complete",
            full_text_access="document_link",
            supported_filters=["text", "exact_phrase", "number", "collection", "page"],
            unsupported_filters=unsupported,
            filter_semantics={
                "text": "local_postfilter",
                "exact_phrase": "local_postfilter",
                "number": "local_postfilter",
                "collection": "route_selection",
                "page": "local_window",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                **{name: "unsupported" for name in unsupported},
            },
            ordering_modes=["source_pdf_order"],
            detail_modes=["compilation_pdf"],
            limitations=[
                (
                    "Compilacao editorial estatica e curada; nao e busca geral nem "
                    "acervo integral do TRT9."
                ),
                (
                    "O PDF contem ementas/decisoes de precedentes qualificados; "
                    "inteiro teor dos votos nao foi demonstrado."
                ),
            ],
            responsible_use=[
                "Usar consultas bounded e preservar a classificacao contextual/opt-in."
            ],
        )

    def _request_pdf(self, query: JurisprudenceQuery, url: str) -> tuple[bytes, SourceTrace]:
        request = TransportRequest(
            source=self.name,
            operation="compilation_fetch",
            method="GET",
            url=url,
            headers={"Accept": "application/pdf"},
            idempotent=True,
        )
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TRT9 NUGEP request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            if response.status is TransportStatus.TIMEOUT:
                raise SourceUnavailableError("TRT9 NUGEP request timeout")
            raise SourceUnavailableError(
                f"TRT9 NUGEP transport failed: {response.error_type or response.status.value}"
            )
        status = response.status_code or 0
        if status == 429:
            raise RateLimitDetectedError("TRT9 NUGEP returned HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TRT9 NUGEP returned HTTP {status}")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TRT9 NUGEP returned HTTP {status}")
        body = bytes(response.body)
        if not body.startswith(b"%PDF"):
            raise ParserContractChangedError("TRT9 NUGEP did not return a PDF")
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET official TRT9 NUGEP jurisprudence PDF",
            query={
                "text": query.text,
                "number": query.number,
                "collection": query.collection,
                "page": query.page,
            },
            source_url=url,
            final_url=response.final_url,
            http_status=status,
            content_type=response.content_type,
            content_sha256=response.content_sha256,
            response_bytes=response.byte_size,
            elapsed_ms=response.elapsed_ms,
            retrieval_status="ok",
            limitations=[
                "Compilacao estatica e curada; total conhecido refere-se apenas ao PDF observado.",
                "Nao ha pagina remota nem total do corpus geral TRT9.",
            ],
        )
        self._last_bytes = body
        self._last_trace = trace
        return body, trace


def parse_trt9_nugepnac_pdf(
    content: bytes,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    collection: str,
) -> list[JurisprudenceResult]:
    if not content.startswith(b"%PDF"):
        raise ParserContractChangedError("TRT9 NUGEP nao e PDF")
    try:
        text = _extract_pdf_text(content)
    except Exception as exc:
        raise ParserContractChangedError("TRT9 NUGEP PDF nao pode ser extraido") from exc
    text = _clean(text)
    matches = list(_CASE_RE.finditer(text))
    if not matches and text:
        raise ParserContractChangedError("TRT9 NUGEP nao expos identificadores de processos")
    results: list[JurisprudenceResult] = []
    seen: set[str] = set()
    for index, match in enumerate(matches[:MAX_RESULTS], start=1):
        number = match.group(0)
        if number in seen:
            continue
        seen.add(number)
        block = text[
            match.start() : matches[index].start() if index < len(matches) else None
        ].strip()
        if not _matches(block, number, query):
            continue
        digest = hashlib.sha1(f"{collection}:{number}".encode()).hexdigest()[:12]
        results.append(
            JurisprudenceResult(
                id=f"trt9-nugepnac-{digest}",
                source="trt9_nugepnac_jurisprudencia",
                court="TRT9",
                type="precedente_qualificado",
                number=number,
                summary=block,
                full_text=None,
                degree="second",
                instance="second",
                branch="labor",
                authority="TRT9",
                collection=collection,
                document_type="precedente_qualificado",
                document_url=trace.source_url,
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.COMPLETE,
                source_trace=trace,
                raw={"source_record_id": f"trt9-{collection.lower()}-{index}", "curated": True},
                field_provenance={
                    "number": {"source": "pdf_text", "confidence": "observed"},
                    "summary": {"source": "pdf_text", "confidence": "observed"},
                    "degree": {"source": "official_collection_scope", "confidence": "validated"},
                },
            )
        )
    return results


def _extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return " ".join((page.extract_text() or "") for page in reader.pages)


def _collection_url(base_url: str, query: JurisprudenceQuery) -> tuple[str, str]:
    requested = _normalize(query.collection)
    if requested in {"trt9_irdr", "trt9_nugep_irdr", "irdr"}:
        collection = "TRT9_NUGEP_IRDR"
        list_type = "DECISOES_IRDR"
    else:
        collection = "TRT9_NUGEP_CURATED"
        list_type = ""
    parts = urlsplit(base_url)
    path = parts.path.replace("pdf-simplificado", "pdf-completo") if list_type else parts.path
    query_items = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key != "listaTipo"
    ]
    if list_type:
        query_items.append(("listaTipo", list_type))
    return collection, urlunsplit(
        (parts.scheme, parts.netloc, path, urlencode(query_items), parts.fragment)
    )


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


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.exact_phrase.strip(), query.number.strip())):
        raise QueryRejectedError("TRT9 NUGEP exige texto, frase ou numero")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TRT9 NUGEP suporta somente segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TRT9 NUGEP suporta somente segunda instancia")
    if query.branch and query.branch.casefold() not in {"labor", "trabalhista"}:
        raise QueryRejectedError("TRT9 pertence ao ramo trabalhista")
    if query.authority and query.authority.casefold() not in {"trt9", "trt-9"}:
        raise QueryRejectedError("a autoridade solicitada nao corresponde ao TRT9")


__all__ = ["Trt9NugepnacJurisprudenciaProvider", "parse_trt9_nugepnac_pdf"]
