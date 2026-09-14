"""TJAL/ESMAL public first-instance sentence bank provider.

The Escola Superior da Magistratura de Alagoas (ESMAL) publishes a small,
curated HTML index of selected first-instance sentences.  The index is a
public search surface, but it is not an exhaustive CJPG corpus and it does
not publish an authoritative total.  This adapter therefore keeps the source
is federated as a clearly labelled partial source and exposes its limitations
explicitly.

Only the official search page and PDF links observed in a result are used.
The provider never enumerates files, follows process-consultation links, or
attempts to bypass access controls.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

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
    CanonicalDocument,
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
MAX_PDF_BYTES = 10_000_000
MAX_PAGES = 300
MAX_RESULTS = 100
MAX_REMOTE_PAGE_SIZE = 20
_SEARCH_HOST = "esmal.tjal.jus.br"
_DOCUMENT_HOST = "intranetlegado.tjal.jus.br"
_OFFICIAL_HOSTS = {_SEARCH_HOST, _DOCUMENT_HOST}
_CATEGORY_CODES = {
    "a": "A",
    "administrativo": "A",
    "c": "C",
    "civil": "C",
    "civel": "C",
    "p": "P",
    "penal": "P",
    "e": "E",
    "eleitoral": "E",
    "v": "V",
    "previdenciario": "V",
    "previdenciário": "V",
    "t": "T",
    "tributario": "T",
    "tributário": "T",
    "d": "D",
    "direitos da infancia e da juventude": "D",
    "infancia": "D",
    "juventude": "D",
    "j": "J",
    "juizados especiais": "J",
    "juizados": "J",
}


class TjalEsmalBancoSentencasProvider(JurisprudenceProvider):
    """Search the official ESMAL selected-sentence index (TJAL/CJPG)."""

    name = "tjal_esmal_banco_sentencas"
    authority = "TJAL"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_http: dict[str, Any] = {}
        self._documents: dict[str, str] = {}
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(_SEARCH_HOST,),
                timeout_seconds=self.config.timeout,
                max_retries=1,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
                max_bytes=MAX_HTML_BYTES,
            ),
            session=self.session,
        )
        self._document_policy = TransportPolicy(
            allowed_hosts=(_DOCUMENT_HOST,),
            timeout_seconds=self.config.timeout,
            max_retries=1,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
            max_bytes=MAX_PDF_BYTES,
        )

    @property
    def search_url(self) -> str:
        return self.config.tjal_esmal_banco_sentencas_url

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        category = _validate_query(query)
        html, trace = self._request_html(query, category)
        results = parse_tjal_esmal_html(html, query=query, trace=trace)
        results = results[:MAX_RESULTS]
        self._documents.update(
            {result.id: result.document_url for result in results if result.document_url}
        )
        page_size = min(query.page_size, MAX_REMOTE_PAGE_SIZE)
        start = (query.page - 1) * page_size
        # ``p`` is a remote page parameter.  The rows in this response already
        # belong to the requested page and must not be sliced a second time.
        page_results = results[:page_size]
        return SearchPage(
            source=self.name,
            total=len(results),
            start=start + 1 if page_results else 0,
            end=start + len(page_results) if page_results else 0,
            page=query.page,
            page_size=page_size,
            results=page_results,
            source_trace=trace,
            pagination_mode="remote_page",
            is_complete=False,
            completeness_reason=(
                "A ESMAL publica uma colecao curada de sentencas selecionadas e "
                "nao informa total autoritativo do acervo."
            ),
            ordering="source_order",
            filters_applied={
                "text": "native",
                "exact_phrase": "native",
                "number": "native",
                "legal_area": "native" if category else "unsupported",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
            },
            total_known=False,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE if page_results else ExtractionStatus.EMPTY,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document = self.get_document(precedent_id)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document.text or "",
                    "content_type": document.content_type or "application/pdf",
                }
            ],
            procedural_follow_url=document.url,
            source_trace=document.source_trace,
            raw={"document_url": document.url},
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        url = self._documents.get(document_id)
        if not url:
            raise SourceUnavailableError("TJAL ESMAL exige documento PDF observado na busca atual")
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != _DOCUMENT_HOST:
            raise ParserContractChangedError("TJAL ESMAL documento fora da allowlist oficial")
        return fetch_document_reference(
            DocumentReference(
                id=document_id,
                source=self.name,
                url=url,
                document_type="sentenca",
                expected_content_types=("application/pdf",),
                decision_id=document_id,
            ),
            policy=self._document_policy,
            session=self.session,
            title="TJAL ESMAL Banco de Sentencas",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        unsupported = [
            "courts",
            "types",
            "case_class",
            "judging_body",
            "rapporteur",
            "all_words",
            "any_words",
            "without_words",
            "party_name",
            "party_document",
            "lawyer_name",
            "oab",
            "updated_from",
            "updated_to",
            "published_from",
            "published_to",
            "judgment_date_from",
            "judgment_date_to",
            "fetch_details",
            "precatory_number",
            "police_document",
            "cda",
            "source_origin",
            "source_origins",
            "document_type",
            "decision_type",
        ]
        supported = [
            "text",
            "exact_phrase",
            "number",
            "legal_area",
            "degree",
            "instance",
            "branch",
            "authority",
            "collection",
            "page",
        ]
        return ProviderCapabilities(
            source=self.name,
            display_name="TJAL ESMAL Banco de Sentencas (CJPG curado)",
            source_url=self.search_url,
            category="court_jurisprudence",
            search_modes=["text", "exact_phrase", "case_number", "legal_area", "page"],
            document_types=["sentenca"],
            content_formats=["html", "pdf", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator=("official selected first-instance sentences; collection=CJPG"),
            extracted_fields=[
                "source_record_id",
                "summary",
                "judgment_date",
                "document_url",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "document_type",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /indexS.php?pag=ler&cat=<category>&text=<term>&p=<page>",
                "GET intranetlegado.tjal.jus.br/bancodesentencas/arquivos/<id>.pdf",
            ],
            supports_full_text=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            # The source passes the technical gates and is safe to include as
            # a partial CJPG collection.  It remains explicitly marked as
            # curated/total-unknown in SearchPage so federation cannot imply
            # exhaustive first-instance coverage.
            supports_unified_search=True,
            opt_in_unified_search=False,
            pagination_mode="remote_page",
            max_remote_page=MAX_PAGES,
            max_remote_page_size=MAX_REMOTE_PAGE_SIZE,
            completeness_contract="curated_html_index_total_unknown",
            full_text_access="document_link",
            supported_filters=supported,
            unsupported_filters=unsupported,
            filter_semantics={
                **{name: "native" for name in ("text", "exact_phrase", "number", "legal_area")},
                **{
                    name: "validated_scope"
                    for name in ("degree", "instance", "branch", "authority", "collection")
                },
                "page": "native",
                **{name: "unsupported" for name in unsupported},
            },
            ordering_modes=["source_order"],
            detail_modes=["linked_official_pdf"],
            limitations=[
                "Colecao curada de sentencas selecionadas; nao representa todo o CJPG do TJAL.",
                "A fonte nao publica total autoritativo nem garante cobertura temporal completa.",
                "O inteiro teor depende do PDF oficial observado na linha de resultado.",
            ],
            responsible_use=[
                "Usar consultas bounded e respeitar o intervalo de requisicoes da fonte.",
                "Nao enumerar arquivos nem seguir links fora da allowlist oficial.",
                "Nao converter bloqueio, timeout ou schema invalido em busca vazia.",
            ],
        )

    def _request_html(
        self, query: JurisprudenceQuery, category: str | None
    ) -> tuple[bytes, SourceTrace]:
        parsed = urlparse(self.search_url)
        if parsed.scheme != "https" or parsed.hostname != _SEARCH_HOST:
            raise ParserContractChangedError("TJAL ESMAL busca fora da allowlist oficial")
        params = {
            "pag": "ler",
            "p": str(query.page),
            "cat": category or "",
            "text": query.exact_phrase or query.text or query.number,
        }
        try:
            response = self.transport.request(
                TransportRequest(
                    source=self.name,
                    operation="search",
                    method="GET",
                    url=self.search_url,
                    params=params,
                    idempotent=True,
                )
            )
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(
                f"TJAL ESMAL Banco de Sentencas request failed: {exc}"
            ) from exc
        if response.status is TransportStatus.RESPONSE_TOO_LARGE:
            raise ParserContractChangedError(
                "TJAL ESMAL nao retornou HTML valido dentro do limite de bytes"
            )
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJAL ESMAL transporte falhou: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJAL ESMAL transporte sem status HTTP")
        body = response.body
        response_url = str(response.final_url or response.url or self.search_url)
        headers = response.headers
        self._last_http = {
            "http_status": status_code,
            "final_url": response_url,
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": response.content_sha256,
            "response_bytes": len(body),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if 200 <= status_code < 300 else "error",
        }
        if status_code == 429:
            raise RateLimitDetectedError("TJAL ESMAL returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TJAL ESMAL returned HTTP {status_code}")
        if status_code < 200 or status_code >= 300:
            raise SourceUnavailableError(f"TJAL ESMAL returned HTTP {status_code}")
        if len(body) > MAX_HTML_BYTES or not _looks_like_html(body):
            raise ParserContractChangedError("TJAL ESMAL nao retornou HTML valido dentro do limite")
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /indexS.php?pag=ler",
            query={"page": query.page, "page_size": query.page_size, **params},
            source_url=response_url,
            limitations=[
                "Banco curado de sentencas selecionadas; total autoritativo desconhecido.",
                "Somente links PDF observados na resposta sao elegiveis para detalhe.",
            ],
            **self._last_http,
        )
        return body, trace


def parse_tjal_esmal_html(
    content: bytes | str, *, query: JurisprudenceQuery, trace: SourceTrace
) -> list[JurisprudenceResult]:
    """Parse result rows from the official ESMAL HTML response."""

    raw = content.encode("utf-8") if isinstance(content, str) else content
    if len(raw) > MAX_HTML_BYTES or not _looks_like_html(raw):
        raise ParserContractChangedError("TJAL ESMAL resposta HTML invalida")
    soup = BeautifulSoup(_decode_html(raw), "html.parser")
    if soup.find("table") is None:
        raise ParserContractChangedError("TJAL ESMAL resposta sem tabela de resultados")
    rows = _result_rows(soup)
    if not rows:
        return []
    results: list[JurisprudenceResult] = []
    for row_index, row in enumerate(rows):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue
        date = _clean(cells[1].get_text(" ", strip=True))
        title = _clean(cells[2].get_text(" ", strip=True))
        link = _pdf_link(row)
        if not title or not link:
            continue
        if not _matches_local_query(title, query):
            continue
        result_id = (
            "tjal-esmal-sentenca-"
            + hashlib.sha256(f"{link}|{date}|{title}".encode()).hexdigest()[:24]
        )
        results.append(
            JurisprudenceResult(
                id=result_id,
                source="tjal_esmal_banco_sentencas",
                court="TJAL",
                type="sentenca",
                summary=title,
                judgment_date=date or None,
                publication_date=date or None,
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.COMPLETE,
                source_trace=trace,
                raw={
                    # The public page has no tribunal-assigned case number.
                    # This deterministic fingerprint is nevertheless a stable
                    # source-record identity for the observed sentence/PDF
                    # tuple and is deliberately preserved as raw provenance.
                    "source_record_id": result_id,
                    "row_index": row_index,
                    "date_raw": date,
                    "title_raw": title,
                    "document_url": link,
                    "search_url": trace.source_url,
                },
                degree="first",
                instance="first",
                branch="state",
                authority="TJAL",
                collection="TJAL_ESMAL_CJPG",
                document_type="sentenca",
                source_origin="tjal_esmal_html",
                document_url=link,
                field_provenance={
                    "source_record_id": {
                        "value": result_id,
                        "method": "deterministic_source_url_date_title_fingerprint",
                    },
                    "degree": {"value": "first", "method": "official_collection_scope"},
                    "instance": {"value": "first", "method": "official_collection_scope"},
                    "judgment_date": {"value": date, "method": "official_result_table"},
                    "document_url": {"value": link, "method": "official_pdf_anchor"},
                },
            )
        )
    return results


def _result_rows(soup: BeautifulSoup) -> list[Tag]:
    rows: list[Tag] = []
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 3 and _pdf_link(row):
                rows.append(row)
    return rows


def _pdf_link(row: Tag) -> str | None:
    for anchor in row.find_all("a"):
        href = str(anchor.get("href") or "").strip()
        if not href:
            continue
        absolute = urljoin("https://" + _SEARCH_HOST + "/", href)
        parsed = urlparse(absolute)
        if (
            parsed.scheme == "https"
            and parsed.hostname == _DOCUMENT_HOST
            and parsed.path.casefold().endswith(".pdf")
            and "/bancodesentencas/arquivos/" in parsed.path.casefold()
        ):
            return absolute
    return None


def _matches_local_query(title: str, query: JurisprudenceQuery) -> bool:
    haystack = _norm(title)
    requested = query.exact_phrase or query.text or query.number
    terms = [term for term in _norm(requested).split() if len(term) >= 3]
    if terms and not all(term in haystack for term in terms):
        return False
    excluded = [term for term in _norm(query.without_words).split() if len(term) >= 3]
    return not any(term in haystack for term in excluded)


def _validate_query(query: JurisprudenceQuery) -> str | None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TJAL ESMAL exige termo, numero ou frase exata")
    if query.degree and _norm(query.degree) not in {"first", "primeiro", "1", "1g"}:
        raise QueryRejectedError("TJAL ESMAL suporta somente primeiro grau")
    if query.instance and _norm(query.instance) not in {"first", "primeiro", "1", "1g"}:
        raise QueryRejectedError("TJAL ESMAL suporta somente instancia de primeiro grau")
    if query.branch and _norm(query.branch) not in {"state", "estadual", "justica estadual"}:
        raise QueryRejectedError("TJAL ESMAL pertence ao ramo estadual")
    if query.authority and _norm(query.authority) not in {"tjal", "alagoas"}:
        raise QueryRejectedError("a autoridade solicitada nao corresponde ao TJAL")
    if query.collection and _norm(query.collection) not in {
        "tjal esmal cjpg",
        "tjal_esmal_banco_sentencas",
        "cjpg",
    }:
        raise QueryRejectedError("colecao TJAL ESMAL desconhecida")
    if query.document_type and _norm(query.document_type) not in {"sentenca", "sentenca 1g"}:
        raise QueryRejectedError("TJAL ESMAL publica somente sentencas")
    if query.legal_area and _norm(query.legal_area) not in _CATEGORY_CODES:
        raise QueryRejectedError("categoria legal_area nao reconhecida pela ESMAL")
    return _CATEGORY_CODES.get(_norm(query.legal_area)) if query.legal_area else None


def _looks_like_html(content: bytes) -> bool:
    sample = content[:4096].lower()
    return b"<html" in sample or b"<!doctype" in sample or b"<table" in sample


def _decode_html(content: bytes) -> str:
    """Prefer UTF-8 when the legacy page's meta charset is stale."""

    for encoding in ("utf-8", "cp1252", "iso-8859-1"):
        try:
            return content.decode(encoding, errors="strict")
        except UnicodeDecodeError:
            continue
    return content.decode("iso-8859-1", errors="replace")


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\ufffd", " ")).strip()


def _norm(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


__all__ = ["TjalEsmalBancoSentencasProvider", "parse_tjal_esmal_html"]
