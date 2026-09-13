"""TJAC public Banco de Sentenças (curated first-instance collection).

The Corregedoria publishes a static HTML index with selected sentence PDFs.
This adapter keeps the source deliberately separate from the general TJAC
e-SAJ jurisprudence surface: it is searchable only by local post-filtering of
the bounded index and is opt-in in federated callers.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urljoin, urlparse

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
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

MAX_INDEX_BYTES = 5_000_000
MAX_RESULTS = 100
_HOST = "www.tjac.jus.br"
_CNJ_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.8\.01\.\d{4}\b")
_PDF_RE = re.compile(r"\.pdf(?:$|[?#])", re.IGNORECASE)


class TjacBancoSentencasProvider(JurisprudenceProvider):
    """Expose TJAC's official selected-sentence index and PDFs."""

    name = "tjac_banco_sentencas"
    authority = "TJAC"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_http: dict[str, Any] = {}
        self._items: dict[str, str] = {}
        host = urlparse(self.index_url).hostname or ""
        self._transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_INDEX_BYTES,
                max_retries=1,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._document_policy = TransportPolicy(
            allowed_hosts=(_HOST,),
            timeout_seconds=self.config.timeout,
            max_bytes=8_000_000,
            max_retries=1,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )

    @property
    def index_url(self) -> str:
        return self.config.tjac_banco_sentencas_url

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        markup, trace = self._request_index(query)
        results = parse_tjac_banco_sentencas(markup, query=query, trace=trace)
        results = results[:MAX_RESULTS]
        for result in results:
            if result.document_url:
                self._items[result.id] = result.document_url
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
            is_complete=False,
            completeness_reason=(
                "indice oficial curado de sentencas; a fonte nao publica total autoritativo "
                "nem busca geral de todo o CJPG"
            ),
            ordering="source_html_order",
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
            total_known=False,
            access_status=AccessStatus.PUBLIC,
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

    def get_document(self, document_id: str):
        url = self._items.get(document_id)
        if not url:
            raise QueryRejectedError("TJAC documento deve ser observado em uma busca")
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != _HOST:
            raise QueryRejectedError("TJAC documento fora do host oficial permitido")
        return fetch_document_reference(
            DocumentReference(
                id=document_id,
                source=self.name,
                url=url,
                document_type="sentenca",
                expected_content_types=("application/pdf", "application/octet-stream"),
                decision_id=document_id,
            ),
            policy=self._document_policy,
            session=self.session,
            title="TJAC Banco de Sentencas",
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
            "legal_area",
            "document_type",
            "decision_type",
            "source_origin",
            "source_origins",
            "precatory_number",
            "police_document",
            "cda",
        ]
        return ProviderCapabilities(
            source=self.name,
            display_name="TJAC Banco de Sentencas (CJPG curado)",
            source_url=self.index_url,
            category="court_jurisprudence",
            search_modes=["text", "exact_phrase", "case_number", "full_text"],
            document_types=["sentenca"],
            content_formats=["html", "pdf", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator="official selected first-instance sentences index",
            extracted_fields=[
                "case_number",
                "judging_body",
                "document_url",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "document_type",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=["GET /coger/banco-de-sentencas/", "GET /wp-content/uploads/...pdf"],
            supports_full_text=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            pagination_mode="local_html_window",
            max_remote_page_size=20,
            completeness_contract="curated_html_index_total_unknown",
            full_text_access="document_link",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "page",
            ],
            unsupported_filters=unsupported,
            filter_semantics={
                "text": "local_postfilter",
                "exact_phrase": "local_postfilter",
                "number": "local_postfilter",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "page": "local_postfilter",
                **{name: "unsupported" for name in unsupported},
            },
            ordering_modes=["source_order"],
            detail_modes=["linked_official_pdf"],
            limitations=[
                "Colecao curada de sentencas selecionadas, nao todo o CJPG do TJAC.",
                "A pagina nao informa total autoritativo nem pagina remota.",
                "Documentos sao buscados somente sob demanda e na allowlist oficial.",
            ],
            responsible_use=[
                "Respeitar limites da fonte e nao tentar acessar documentos nao publicados.",
                (
                    "Nao seguir consultas processuais nem inferir cobertura nacional "
                    "a partir do banco."
                ),
            ],
        )

    def _request_index(self, query: JurisprudenceQuery) -> tuple[str, SourceTrace]:
        parsed = urlparse(self.index_url)
        if parsed.scheme != "https" or parsed.hostname != _HOST:
            raise QueryRejectedError("TJAC indice fora da allowlist oficial")
        response = self._transport.request(
            TransportRequest(
                source=self.name,
                operation="tjac_selected_sentence_index",
                method="GET",
                url=self.index_url,
                headers={"Accept": "text/html,application/xhtml+xml"},
                idempotent=True,
            )
        )
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(f"TJAC Banco transport failed: {response.status.value}")
        status = int(response.status_code or 0)
        body = bytes(response.body)
        self._last_http = {
            "http_status": status,
            "final_url": str(response.final_url or self.index_url),
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if 200 <= status < 300 else "error",
        }
        if status == 429:
            raise RateLimitDetectedError("TJAC Banco returned HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TJAC Banco returned HTTP {status}")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TJAC Banco returned HTTP {status}")
        if not body:
            raise ParserContractChangedError("TJAC Banco returned empty HTML")
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /coger/banco-de-sentencas/",
            query={"text": query.text, "number": query.number, "page": query.page},
            source_url=self.index_url,
            limitations=[
                "Indice oficial curado de sentencas selecionadas; total desconhecido.",
                "PDFs somente sao buscados quando o chamador solicita o documento.",
            ],
            **self._last_http,
        )
        return body.decode("utf-8", "replace"), trace


def parse_tjac_banco_sentencas(
    markup: str, *, query: JurisprudenceQuery, trace: SourceTrace
) -> list[JurisprudenceResult]:
    soup = BeautifulSoup(markup, "html.parser")
    results: list[JurisprudenceResult] = []
    for index, anchor in enumerate(soup.select("a[href]")):
        href = str(anchor.get("href") or "").strip()
        url = urljoin(trace.source_url or "https://www.tjac.jus.br/", href)
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != _HOST or not _PDF_RE.search(parsed.path):
            continue
        context = _anchor_context(anchor)
        case_match = _CNJ_RE.search(context) or _CNJ_RE.search(url)
        case_number = case_match.group(0) if case_match else None
        if not _matches_query(query, context, case_number):
            continue
        source_id = f"tjac-cjpg-{case_number or hashlib.sha256(url.encode()).hexdigest()[:16]}"
        results.append(
            JurisprudenceResult(
                id=source_id,
                source="tjac_banco_sentencas",
                court="TJAC",
                type="sentenca",
                number=case_number,
                summary=context or None,
                access_status=AccessStatus.PUBLIC,
                source_trace=trace,
                raw={"index": index, "context": context, "document_url": url},
                degree="first",
                instance="first",
                branch="state",
                authority="TJAC",
                collection="CJPG",
                document_type="sentenca",
                source_origin="official_selected_sentence_index",
                document_url=url,
                field_provenance={
                    "case_number": {"source": "official_index_visible_text"},
                    "document_url": {"source": "official_index_href"},
                    "degree": {"source": "source_contract:tjac_banco_sentencas"},
                },
            )
        )
    return results


def _anchor_context(anchor: Any) -> str:
    parent = anchor.parent
    text = (
        parent.get_text(" ", strip=True) if parent is not None else anchor.get_text(" ", strip=True)
    )
    return " ".join(str(text).split())


def _matches_query(query: JurisprudenceQuery, context: str, case_number: str | None) -> bool:
    if query.number and query.number.casefold() not in (case_number or context).casefold():
        return False
    term = (query.exact_phrase or query.text or "").strip()
    return not term or term.casefold() in context.casefold()


def _validate_query(query: JurisprudenceQuery) -> None:
    if query.page < 1 or query.page_size < 1 or query.page_size > 20:
        raise QueryRejectedError("TJAC Banco aceita page_size entre 1 e 20")
    if query.degree and query.degree.casefold() not in {"first", "primeiro", "1", "primeiro grau"}:
        raise QueryRejectedError("TJAC Banco e uma superficie de primeiro grau")
    if query.instance and query.instance.casefold() not in {"first", "primeiro", "1"}:
        raise QueryRejectedError("TJAC Banco e uma superficie de primeira instancia")
    if query.authority and query.authority.upper() != "TJAC":
        raise QueryRejectedError("TJAC Banco aceita apenas authority=TJAC")
