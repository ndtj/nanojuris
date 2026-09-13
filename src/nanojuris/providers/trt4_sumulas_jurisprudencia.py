"""TRT4 official curated appellate jurisprudence page.

The TRT4 portal publishes its súmulas and related appellate materials as a
public HTML collection with links to the official resolutions/acórdãos.  This
adapter intentionally exposes that collection as contextual, opt-in data: it
is not the Falcão full-text search corpus and does not claim complete TRT4
coverage.  The page is fetched once per search and records are filtered
locally, preserving explicit transport/parser failures.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import DocumentReference, fetch_document_reference
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

MAX_HTML_BYTES = 2_000_000
MAX_RESULTS = 500
_HOST = "www.trt4.jus.br"
_SUMULA_RE = re.compile(r"s[úu]mula\s+n[ºo°]?\s*([0-9]+)", re.IGNORECASE)
_OJ_RE = re.compile(r"orienta[cç][aã]o\s+jurisprudencial\s*(?:n[ºo°]?\s*)?([0-9]+)", re.IGNORECASE)
_CASE_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.5\.04\.\d{4}\b")


class Trt4SumulasJurisprudenciaProvider(JurisprudenceProvider):
    """Search the bounded official TRT4 súmulas/precedents HTML page."""

    name = "trt4_sumulas_jurisprudencia"
    authority = "TRT4"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlsplit(self.config.trt4_sumulas_jurisprudencia_url).hostname or _HOST
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_HTML_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._observed: dict[str, str] = {}
        self._observed_summary: dict[str, str] = {}
        self._last_trace: SourceTrace | None = None

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        content, trace = self._request_page(query)
        results = parse_trt4_sumulas_html(content, query=query, trace=trace)
        for result in results:
            if result.document_url:
                self._observed[result.id] = result.document_url
            self._observed_summary[result.id] = result.summary or ""
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
            pagination_mode="local_html_window",
            is_complete=True,
            completeness_reason=(
                "Pagina oficial de colecao curada carregada integralmente; o total nao "
                "representa o corpus geral do TRT4."
            ),
            ordering="source_html_order",
            filters_applied={
                "text": "local_postfilter",
                "exact_phrase": "local_postfilter",
                "number": "local_postfilter",
                "document_type": "local_postfilter",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
            },
            total_known=True,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        if precedent_id not in self._observed:
            raise SourceUnavailableError("TRT4 documento exige resultado observado na sessao")
        summary = self._observed_summary.get(precedent_id, "")
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": summary, "content_type": "text/plain"}] if summary else [],
            source_trace=self._last_trace,
            raw={"collection": "TRT4_SUMULAS", "curated": True},
        )

    def get_document(self, document_id: str):
        url = self._observed.get(document_id)
        if not url:
            raise SourceUnavailableError("TRT4 documento exige identificador observado")
        return fetch_document_reference(
            DocumentReference(
                id=document_id,
                source=self.name,
                url=url,
                document_type="sumula_ou_precedente",
                expected_content_types=("application/pdf", "text/html", "application/octet-stream"),
                decision_id=document_id,
            ),
            policy=self.transport.policy,
            session=self.session,
            title="TRT4 Súmulas e precedentes",
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
            display_name="TRT4 Súmulas e precedentes (coleção curada)",
            source_url=self.config.trt4_sumulas_jurisprudencia_url,
            category="curated_jurisprudence",
            search_modes=["text", "exact_phrase", "case_number", "pagination"],
            document_types=["sumula", "orientacao_jurisprudencial", "acordao"],
            content_formats=["html", "pdf", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator="authority=TRT4;branch=labor;degree=second;collection=TRT4_SUMULAS",
            extracted_fields=[
                "case_number",
                "summary",
                "document_url",
                "document_type",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=["GET official TRT4 súmulas HTML"],
            supports_full_text=False,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            pagination_mode="local_html_window",
            max_remote_page_size=100,
            completeness_contract="static_curated_html_total_known_not_corpus_complete",
            full_text_access="document_link",
            supported_filters=["text", "exact_phrase", "number", "document_type", "page"],
            unsupported_filters=unsupported,
            filter_semantics={
                "text": "local_postfilter",
                "exact_phrase": "local_postfilter",
                "number": "local_postfilter",
                "document_type": "local_postfilter",
                "page": "local_window",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                **{name: "unsupported" for name in unsupported},
            },
            ordering_modes=["source_html_order"],
            detail_modes=["official_document_link"],
            limitations=[
                (
                    "Colecao estatica e curada; nao e a busca geral Falcao nem o acervo "
                    "integral do TRT4."
                ),
                (
                    "O inteiro teor depende do documento oficial vinculado e nao foi "
                    "incorporado ao resultado."
                ),
            ],
            responsible_use=[
                "Usar consultas bounded e preservar a classificacao contextual/opt-in."
            ],
        )

    def _request_page(self, query: JurisprudenceQuery) -> tuple[bytes, SourceTrace]:
        request = TransportRequest(
            source=self.name,
            operation="curated_page_fetch",
            method="GET",
            url=self.config.trt4_sumulas_jurisprudencia_url,
            headers={"Accept": "text/html"},
            idempotent=True,
        )
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TRT4 sumulas request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            if response.status is TransportStatus.TIMEOUT:
                raise SourceUnavailableError("TRT4 sumulas request timeout")
            raise SourceUnavailableError(
                f"TRT4 sumulas transport failed: {response.error_type or response.status.value}"
            )
        status = response.status_code or 0
        if status == 429:
            raise RateLimitDetectedError("TRT4 sumulas returned HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TRT4 sumulas returned HTTP {status}")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TRT4 sumulas returned HTTP {status}")
        body = bytes(response.body)
        if b"<html" not in body[:4096].lower() and b"<!doctype" not in body[:4096].lower():
            raise ParserContractChangedError("TRT4 sumulas did not return HTML")
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET official TRT4 súmulas HTML",
            query={"text": query.text, "number": query.number, "page": query.page},
            source_url=response.final_url or self.config.trt4_sumulas_jurisprudencia_url,
            final_url=response.final_url,
            http_status=status,
            content_type=response.content_type,
            content_sha256=response.content_sha256,
            response_bytes=response.byte_size,
            elapsed_ms=response.elapsed_ms,
            retrieval_status="ok",
            limitations=[
                "Pagina estatica e curada; total conhecido refere-se somente a esta pagina.",
                "A busca geral Falcao do TRT4 nao e consultada por este adapter.",
            ],
        )
        self._last_trace = trace
        return body, trace


def parse_trt4_sumulas_html(
    content: bytes,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
) -> list[JurisprudenceResult]:
    try:
        soup = BeautifulSoup(content, "html.parser")
    except Exception as exc:
        raise ParserContractChangedError("TRT4 sumulas HTML nao pode ser analisado") from exc
    candidates: list[tuple[str, str, str]] = []
    seen_keys: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(trace.source_url or "https://www.trt4.jus.br", str(anchor["href"]))
        if not (
            href.startswith("https://www.trt4.jus.br/")
            or href.startswith("https://pesquisatextual.trt4.jus.br/")
        ):
            continue
        anchor_text = _clean(anchor.get_text(" ", strip=True))
        parent = anchor.parent
        context = _clean(parent.get_text(" ", strip=True)) if parent else anchor_text
        text = context if len(context) >= len(anchor_text) else anchor_text
        sumula = _SUMULA_RE.search(text)
        oj = _OJ_RE.search(text)
        case = _CASE_RE.search(text) or _CASE_RE.search(anchor_text)
        if sumula:
            key = f"sumula:{sumula.group(1)}"
            kind = "sumula"
        elif oj:
            key = f"oj:{oj.group(1)}"
            kind = "orientacao_jurisprudencial"
        elif case and ("acord" in _normalize(text) or "iuj" in _normalize(text)):
            key = f"case:{case.group(0)}"
            kind = "acordao"
        else:
            continue
        if key in seen_keys:
            continue
        seen_keys.add(key)
        candidates.append((key, kind, text))
        if len(candidates) >= MAX_RESULTS:
            break
    if not candidates:
        raise ParserContractChangedError("TRT4 sumulas nao expos registros curados")
    results: list[JurisprudenceResult] = []
    for key, kind, text in candidates:
        number = _CASE_RE.search(text)
        if not _matches(text, number.group(0) if number else key, query, kind=kind):
            continue
        digest = hashlib.sha1(key.encode()).hexdigest()[:12]
        result_id = f"trt4-sumulas-{digest}"
        anchor = _find_anchor_for_key(soup, key)
        document_url = (
            urljoin(trace.source_url or "https://www.trt4.jus.br", anchor.get("href", ""))
            if anchor is not None
            else None
        )
        results.append(
            JurisprudenceResult(
                id=result_id,
                source="trt4_sumulas_jurisprudencia",
                court="TRT4",
                type=kind,
                number=number.group(0) if number else None,
                summary=text,
                full_text=None,
                degree="second",
                instance="second",
                branch="labor",
                authority="TRT4",
                collection="TRT4_SUMULAS",
                document_type=kind,
                document_url=document_url,
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.PARTIAL,
                source_trace=trace,
                raw={"source_record_id": key, "curated": True},
                field_provenance={
                    "summary": {"source": "official_html", "confidence": "observed"},
                    "degree": {"source": "official_collection_scope", "confidence": "validated"},
                },
            )
        )
    return results


def _find_anchor_for_key(soup: BeautifulSoup, key: str):
    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href", "")).strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        text = _clean(
            anchor.parent.get_text(" ", strip=True)
            if anchor.parent
            else anchor.get_text(" ", strip=True)
        )
        sumula = _SUMULA_RE.search(text)
        if key.startswith("sumula:") and sumula and sumula.group(1) == key.split(":", 1)[1]:
            return anchor
        oj = _OJ_RE.search(text)
        if key.startswith("oj:") and oj and oj.group(1) == key.split(":", 1)[1]:
            return anchor
        if key.startswith("case:") and key.split(":", 1)[1] in text:
            return anchor
    return None


def _matches(text: str, number: str, query: JurisprudenceQuery, *, kind: str = "") -> bool:
    normalized = _normalize(text)
    if query.number and _normalize(query.number) not in _normalize(number):
        return False
    if query.document_type and _normalize(query.document_type) not in _normalize(kind):
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
        raise QueryRejectedError("TRT4 sumulas exige texto, frase ou numero")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TRT4 sumulas suporta somente segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TRT4 sumulas suporta somente segunda instancia")
    if query.branch and query.branch.casefold() not in {"labor", "trabalhista"}:
        raise QueryRejectedError("TRT4 pertence ao ramo trabalhista")
    if query.authority and query.authority.casefold() not in {"trt4", "trt-4"}:
        raise QueryRejectedError("a autoridade solicitada nao corresponde ao TRT4")


__all__ = ["Trt4SumulasJurisprudenciaProvider", "parse_trt4_sumulas_html"]
