"""TJRJ Banco de Sentenças selected first-instance collection.

The Tribunal de Justiça do Rio de Janeiro publishes an official PDF index of
selected first-instance sentences.  The index contains topic labels, CNJ
numbers and links to public ``.doc``/``.docx`` decisions.  It is a curated
collection, not a complete CJPG search endpoint, so this provider is bounded
and opt-in.  It never follows the process-lookup links in the PDF and never
tries to bypass access controls on the document host.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from io import BytesIO
from typing import Any
from urllib.parse import urlparse

import requests
from pypdf import PdfReader

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
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus

MAX_INDEX_BYTES = 5_000_000
MAX_INDEX_PAGES = 300
MAX_RESULTS = 100
_HOST = "portaltj.tjrj.jus.br"
_DOCUMENT_HOST = "www4.tjrj.jus.br"
_OFFICIAL_HOSTS = {_HOST, _DOCUMENT_HOST}
_CASE_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.8\.19\.\d{4}\b")
_PROCESS_LABEL_RE = re.compile(r"PROCESSO\s*:?\s*", re.I)
_DOCUMENT_RE = re.compile(r"/AtosOficiais/bancodesentencas/[^\s?#]+\.(?:docx?|DOCX?)")
_NOISE = re.compile(r"^(?:\d+|\(topo\)|senten[cç][aã]o|processo\s*:?)$", re.I)


class TjrjBancoSentencasProvider(JurisprudenceProvider):
    """Search the official TJRJ selected-sentence index bounded in memory."""

    name = "tjrj_banco_sentencas"
    authority = "TJRJ"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_http: dict[str, Any] = {}
        self._items: dict[str, dict[str, Any]] = {}
        self._index_transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(_HOST,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_INDEX_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
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
            max_bytes=MAX_INDEX_BYTES,
        )

    @property
    def index_url(self) -> str:
        return self.config.tjrj_banco_sentencas_url

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        body, trace = self._request_index(query)
        entries = parse_tjrj_banco_sentencas_pdf(body, query=query, trace=trace)
        entries = entries[:MAX_RESULTS]
        for result in entries:
            self._items[result.id] = {
                "document_url": result.document_url,
                "trace": trace,
            }
        start = (query.page - 1) * query.page_size
        page_results = entries[start : start + query.page_size]
        return SearchPage(
            source=self.name,
            total=len(entries),
            start=start + 1 if page_results else 0,
            end=start + len(page_results) if page_results else 0,
            page=query.page,
            page_size=query.page_size,
            results=page_results,
            source_trace=trace,
            pagination_mode="local_pdf_window",
            is_complete=False,
            completeness_reason=(
                "A fonte publica um banco curado de sentencas selecionadas; "
                "nao informa total de acervo nem oferece busca nacional completa."
            ),
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
            total_known=False,
            access_status=AccessStatus.PUBLIC,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        item = self._items.get(precedent_id)
        if item is None or not item.get("document_url"):
            raise SourceUnavailableError("TJRJ Banco exige documento observado na sessao")
        document = self.get_document(precedent_id)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document.text or "",
                    "content_type": document.content_type or "application/octet-stream",
                }
            ],
            procedural_follow_url=document.url,
            source_trace=document.source_trace,
            raw={"document_url": document.url},
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str):
        item = self._items.get(document_id)
        if item is None or not item.get("document_url"):
            raise SourceUnavailableError("TJRJ Banco documento nao observado")
        url = str(item["document_url"])
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != _DOCUMENT_HOST:
            raise ParserContractChangedError("TJRJ documento fora da allowlist oficial")
        return fetch_document_reference(
            DocumentReference(
                id=document_id,
                source=self.name,
                url=url,
                expected_content_types=(
                    "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "application/octet-stream",
                    "text/html",
                    "application/pdf",
                ),
                decision_id=document_id,
            ),
            policy=self._document_policy,
            session=self.session,
            title="TJRJ Banco de Sentencas selecionadas",
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
            "legal_area",
            "document_type",
            "decision_type",
        ]
        return ProviderCapabilities(
            source=self.name,
            display_name="TJRJ Banco de Sentencas selecionadas (CJPG curado)",
            source_url=self.index_url,
            category="court_jurisprudence",
            search_modes=["text", "exact_phrase", "case_number", "full_text"],
            document_types=["sentenca"],
            content_formats=["pdf", "doc", "docx", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator="official selected first-instance sentences index",
            extracted_fields=[
                "source_record_id",
                "case_number",
                "summary",
                "document_url",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "document_type",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=["GET official banco-sentencas.pdf", "GET linked .doc/.docx"],
            supports_full_text=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            pagination_mode="local_pdf_window",
            max_remote_page_size=20,
            completeness_contract="curated_pdf_index_total_unknown",
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
                **{name: "unsupported" for name in unsupported},
            },
            ordering_modes=["source_order"],
            detail_modes=["linked_official_document"],
            limitations=[
                "Colecao curada de sentencas selecionadas, nao todo o CJPG do TJRJ.",
                "O PDF nao informa total autoritativo nem oferece paginação remota.",
                "Os documentos historicos podem responder 503 ou exigir rota oficial distinta.",
            ],
            responsible_use=[
                "Consultar uma vez por janela e respeitar o limite da fonte.",
                "Nao seguir links de consulta processual presentes no indice.",
                "Nao tentar contornar bloqueios do host de documentos.",
            ],
        )

    def _request_index(self, query: JurisprudenceQuery) -> tuple[bytes, SourceTrace]:
        parsed_index = urlparse(self.index_url)
        if parsed_index.scheme != "https" or (parsed_index.hostname or "").lower() != _HOST:
            raise QueryRejectedError("TJRJ indice fora da allowlist oficial")
        response = self._index_transport.request(
            TransportRequest(
                source=self.name,
                operation="tjrj_selected_sentence_index",
                method="GET",
                url=self.index_url,
                headers={"Accept": "application/pdf"},
                idempotent=True,
            )
        )
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJRJ Banco de Sentencas transport failed: {response.status.value}"
            )
        final = urlparse(str(response.final_url or self.index_url))
        if final.scheme != "https" or (final.hostname or "").lower() != _HOST:
            raise SourceUnavailableError("TJRJ indice redirecionou para host nao autorizado")
        body = response.body
        status = int(response.status_code or 0)
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
            raise RateLimitDetectedError("TJRJ Banco de Sentencas returned HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TJRJ Banco de Sentencas returned HTTP {status}")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TJRJ Banco de Sentencas returned HTTP {status}")
        if len(body) > MAX_INDEX_BYTES or not body.startswith(b"%PDF-"):
            raise ParserContractChangedError("TJRJ Banco nao retornou PDF valido dentro do limite")
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /documents/10136/18187/banco-sentencas.pdf",
            query={"text": query.text, "number": query.number, "page": query.page},
            source_url=self.index_url,
            limitations=[
                "Indice oficial de sentencas selecionadas; total de acervo desconhecido.",
                "Nenhum link de consulta processual e seguido pelo adapter.",
            ],
            **self._last_http,
        )
        return body, trace


def parse_tjrj_banco_sentencas_pdf(
    content: bytes, *, query: JurisprudenceQuery, trace: SourceTrace
) -> list[JurisprudenceResult]:
    """Parse the public index without persisting a searchable corpus."""

    try:
        reader = PdfReader(BytesIO(content), strict=False)
    except Exception as exc:  # noqa: BLE001
        raise ParserContractChangedError("TJRJ Banco PDF malformado") from exc
    if len(reader.pages) > MAX_INDEX_PAGES:
        raise ParserContractChangedError("TJRJ Banco PDF excede o limite de paginas")
    pages = [(str(page.extract_text() or ""), _document_links(page)) for page in reader.pages]
    return parse_tjrj_banco_sentencas_pages(pages, query=query, trace=trace)


def parse_tjrj_banco_sentencas_pages(
    pages: list[tuple[str, list[str]]], *, query: JurisprudenceQuery, trace: SourceTrace
) -> list[JurisprudenceResult]:
    """Parse extracted page text and observed document annotations.

    This seam keeps parser tests deterministic and prevents fixtures from
    depending on the binary PDF renderer.  Production still obtains ``pages``
    only from the bounded official PDF above.
    """

    terms = _query_terms(query)
    results: list[JurisprudenceResult] = []
    for page_number, (text, document_urls) in enumerate(pages, 1):
        if not text.strip():
            continue
        safe_document_urls = [
            url if _is_allowlisted_document_url(url) else None for url in document_urls
        ]
        page_norm = _norm(text)
        if query.number and _norm(query.number) not in page_norm:
            continue
        if terms and not all(term in page_norm for term in terms):
            continue
        if query.without_words and any(
            term in page_norm for term in _query_terms_text(query.without_words)
        ):
            continue
        cases = list(_CASE_RE.finditer(text))
        for index, match in enumerate(cases):
            case_number = match.group(0)
            document_url = safe_document_urls[index] if index < len(safe_document_urls) else None
            context = _entry_context(text, match.start())
            identity_material = "|".join((case_number, document_url or "", _norm(context)))
            result_id = (
                "tjrj-banco-sentencas-"
                + hashlib.sha256(identity_material.encode("utf-8")).hexdigest()[:20]
            )
            results.append(
                JurisprudenceResult(
                    id=result_id,
                    source="tjrj_banco_sentencas",
                    court="TJRJ",
                    type="sentenca",
                    number=case_number,
                    summary=context or "Sentenca selecionada no banco oficial TJRJ.",
                    access_status=AccessStatus.PUBLIC,
                    source_trace=trace,
                    raw={
                        "source_record_id": result_id,
                        "index_url": trace.source_url,
                        "pdf_page": page_number,
                        "selected_sentence_index": index,
                        "document_link_observed": document_url is not None,
                    },
                    degree="first",
                    instance="first",
                    branch="state",
                    authority="TJRJ",
                    collection="TJRJ_BANCO_SENTENCAS",
                    document_type="sentenca",
                    source_origin="tjrj_banco_sentencas_pdf",
                    document_url=document_url,
                    field_provenance={
                        "source_record_id": {
                            "value": result_id,
                            "method": "case_number_document_url_context_fingerprint",
                        },
                        "degree": {"value": "first", "method": "official_collection_scope"},
                        "instance": {"value": "first", "method": "official_collection_scope"},
                        "document_url": {
                            "value": document_url,
                            "method": "pdf_annotation_allowlisted",
                        },
                    },
                )
            )
    return results


def _document_links(page: Any) -> list[str]:
    raw = page.get("/Annots")
    annotations = raw.get_object() if raw else []
    links: list[str] = []
    for annotation in annotations:
        try:
            action = annotation.get_object().get("/A") or {}
            uri = str(action.get("/URI") or "")
        except Exception:  # noqa: BLE001
            continue
        if not _is_allowlisted_document_url(uri):
            continue
        links.append(uri.replace("http://", "https://", 1))
    return links


def _is_allowlisted_document_url(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme in {"http", "https"}
        and parsed.hostname == _DOCUMENT_HOST
        and "/atosoficiais/bancodesentencas/" in parsed.path.casefold()
        and parsed.path.casefold().endswith((".doc", ".docx"))
    )


def _entry_context(text: str, start: int) -> str:
    before = text[max(0, start - 420) : start]
    lines = [_normalize(line) for line in before.splitlines()]
    useful = [line for line in lines if line and not _NOISE.match(line)]
    return " ".join(useful[-4:])[:500]


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TJRJ Banco exige termo, numero ou frase exata")
    if query.degree and _norm(query.degree) not in {"first", "primeiro", "1", "1g"}:
        raise QueryRejectedError("TJRJ Banco suporta somente primeiro grau")
    if query.instance and _norm(query.instance) not in {"first", "primeiro", "1", "1g"}:
        raise QueryRejectedError("TJRJ Banco suporta somente instancia de primeiro grau")
    if query.branch and _norm(query.branch) not in {"state", "estadual", "justica estadual"}:
        raise QueryRejectedError("TJRJ Banco pertence ao ramo estadual")
    if query.authority and _norm(query.authority) not in {"tjrj", "rio de janeiro"}:
        raise QueryRejectedError("a autoridade solicitada nao corresponde ao TJRJ")
    if query.collection and _norm(query.collection) not in {
        "tjrj banco sentencas",
        "tjrj_banco_sentencas",
        "cjpg",
    }:
        raise QueryRejectedError("colecao TJRJ Banco desconhecida")


def _query_terms(query: JurisprudenceQuery) -> list[str]:
    raw = query.exact_phrase or query.text or query.number
    return _query_terms_text(raw)


def _query_terms_text(value: str) -> list[str]:
    return [term for term in _norm(value).split() if len(term) >= 3]


def _norm(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\ufffd", " ")).strip()


__all__ = [
    "TjrjBancoSentencasProvider",
    "parse_tjrj_banco_sentencas_pages",
    "parse_tjrj_banco_sentencas_pdf",
]
