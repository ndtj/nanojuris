"""TJMG Digital Library public jurisprudence adapter.

The TJMG legacy search form is protected by a numeric CAPTCHA.  The official
Digital Library exposes a separate, public and searchable collection of
individual jurisprudence records; this adapter uses only that API and keeps
the protected form out of the request path.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import build_canonical_document
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
from nanojuris.transport import (
    SharedHttpClient,
    TransportPolicy,
    TransportRequest,
    TransportResponse,
    TransportStatus,
)

SEARCH_PATH = "/server/api/discover/search/objects"
MAX_PAGE_SIZE = 20
MAX_DOCUMENT_BYTES = 20_000_000
_CASE_RE = re.compile(r"\b\d\.\d{4}\.\d{2}\.\d{4,6}-\d/\d{3}\b")

COLLECTIONS = {
    "civil": "f1196b07-020f-42b2-9e1d-b1e78e7de623",
    "criminal": "1b5765c2-8b53-40f4-aefe-640defb2093f",
    "special": "8e1a4e99-b72a-4382-9a68-ec3d5a6c8066",
}


class TjmgDspaceJurisprudenciaProvider(JurisprudenceProvider):
    """Search individual TJMG second-degree records in the public repository."""

    name = "tjmg_dspace_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_http: dict[str, Any] = {}
        self._items: dict[str, dict[str, Any]] = {}
        host = urlparse(self.config.tjmg_dspace_jurisprudencia_url).hostname or "bd.tjmg.jus.br"
        self._transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_DOCUMENT_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    @property
    def base_url(self) -> str:
        return self.config.tjmg_dspace_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        term = query.exact_phrase or query.text or query.number
        page_size = min(max(query.page_size, 1), MAX_PAGE_SIZE)
        remote_page = max(query.page - 1, 0)
        records: list[JurisprudenceResult] = []
        totals: list[int] = []
        traces: list[SourceTrace] = []
        for collection, scope in COLLECTIONS.items():
            payload = {
                "query": term,
                "scope": scope,
                "size": page_size,
                "page": remote_page,
                "sort": "dc.date.issued,DESC",
            }
            data = self._request_json(payload)
            page_data = _search_page(data)
            if page_data["total"] is not None:
                totals.append(page_data["total"])
            trace = self._trace(query, collection, payload)
            traces.append(trace)
            for item in page_data["items"]:
                result = _parse_item(item, trace, self.base_url)
                if result is None:
                    continue
                records.append(result)
                self._items[result.id] = {
                    "item_url": item["item_url"],
                    "metadata": item["metadata"],
                    "trace": trace,
                }
        records.sort(key=lambda item: (item.publication_date or "", item.id), reverse=True)
        # The remote page is shared by three collections. Keep the offset
        # visible and deterministic without claiming a cross-collection total
        # that the source does not expose as one query.
        start = (query.page - 1) * page_size
        page_results = records[start : start + page_size]
        total = sum(totals) if len(totals) == len(COLLECTIONS) else len(records)
        total_known = len(totals) == len(COLLECTIONS)
        primary_trace: SourceTrace | None = traces[0] if traces else None
        if primary_trace is not None and len(traces) > 1:
            primary_trace.query["scopes"] = list(COLLECTIONS)
        complete = total_known and start + len(page_results) >= total
        return SearchPage(
            source=self.name,
            total=total,
            start=start,
            end=start + len(page_results),
            page=query.page,
            page_size=page_size,
            results=page_results,
            source_trace=primary_trace,
            pagination_mode="merged_collection_page",
            is_complete=complete,
            completeness_reason=(
                "totais somados das coleções cível, criminal e órgão especial"
                if total_known
                else "uma ou mais coleções não informaram total"
            ),
            ordering="publication_date_desc_then_id",
            filters_applied={
                "text": "native",
                "exact_phrase": "native_as_query",
                "number": "native_as_query",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
            },
            total_known=total_known,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document = self.get_document(precedent_id)
        text = document.text or ""
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": text,
                    "content_type": "text/plain",
                    "source_content_type": document.content_type,
                }
            ],
            procedural_follow_url=document.url,
            source_trace=document.source_trace,
            raw={"document_url": document.url, "pdf_bytes": document.byte_size},
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        item = self._items.get(document_id)
        if item is None:
            raise SourceUnavailableError(
                "TJMG Digital Library detalhe disponível somente após search"
            )
        bitstream_url = self._resolve_bitstream(item["item_url"])
        content = self._request_bytes(bitstream_url)
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="acordao",
            content=content,
            content_type=self._last_http.get("content_type") or "application/pdf",
            title=_first(item["metadata"], "dc.title"),
            url=bitstream_url,
            source_trace=self._detail_trace(item["trace"], bitstream_url),
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"item_url": item["item_url"], "repository": self.base_url},
            parser="tjmg_dspace_jurisprudencia.pdf",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJMG Biblioteca Digital — Jurisprudência (CJSG)",
            source_url=f"{self.base_url}/handle/tjmg/6306",
            category="court_jurisprudence",
            search_modes=["text", "case_number", "summary", "date_range", "pagination"],
            document_types=["acordao", "ementa"],
            content_formats=["json", "pdf", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator=(
                "TJMG Digital Library collections; second-degree chamber records"
            ),
            extracted_fields=[
                "case_number",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "full_text",
                "document_url",
                "degree",
                "instance",
                "collection",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /server/api/discover/search/objects",
                "GET /server/api/core/items/{uuid}",
                "GET /server/api/core/items/{uuid}/bundles",
                "GET /server/api/core/bitstreams/{uuid}/content",
            ],
            supports_full_text=True,
            full_text_access="document_link",
            supports_unified_search=True,
            supports_mcp=True,
            supports_cli=True,
            supports_live_tests=True,
            pagination_mode="merged_collection_page",
            max_remote_page_size=MAX_PAGE_SIZE,
            completeness_contract="sum_of_three_public_collection_totals",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "degree",
                "instance",
                "branch",
                "page",
            ],
            unsupported_filters=[
                "courts",
                "types",
                "all_words",
                "any_words",
                "without_words",
                "case_class",
                "rapporteur",
                "judging_body",
                "party_name",
                "party_document",
                "lawyer_name",
                "oab",
                "precatory_number",
                "police_document",
                "cda",
                "source_origin",
                "source_origins",
                "fetch_details",
                "legal_area",
                "published_from",
                "published_to",
                "judgment_date_from",
                "judgment_date_to",
                "updated_from",
                "updated_to",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "native_as_query",
                "number": "native_as_query",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "page": "native",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "decision_type": "validated_scope",
                "case_class": "unsupported",
                "rapporteur": "unsupported",
                "judging_body": "unsupported",
                "types": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "party_document": "unsupported",
                "lawyer_name": "unsupported",
                "oab": "unsupported",
                "precatory_number": "unsupported",
                "police_document": "unsupported",
                "cda": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
                "fetch_details": "unsupported",
                "legal_area": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
            },
            limitations=[
                "A API combina três coleções e não oferece um total único por consulta.",
                "O acervo é o repositório público da Biblioteca Digital, não o espelho "
                "completo do formulário protegido.",
                "O PDF e a ementa são preservados; disponibilidade de voto integral "
                "depende do item.",
            ],
            responsible_use=["Usar chamadas públicas bounded e respeitar o rate limit da fonte."],
        )

    def _request_json(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._request(SEARCH_PATH, params=params)
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJMG DSpace retornou JSON inválido") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJMG DSpace retornou envelope inesperado")
        return data

    def _request_bytes(self, url: str) -> bytes:
        response = self._request(url)
        body = response.body
        if len(body) > MAX_DOCUMENT_BYTES:
            raise SourceUnavailableError("TJMG DSpace documento excede limite de tamanho")
        return body

    def _request(self, path: str, **kwargs: Any) -> TransportResponse:
        url = path if path.startswith("http") else urljoin(self.base_url + "/", path.lstrip("/"))
        response = self._transport.request(
            TransportRequest(
                source=self.name,
                operation="dspace_request",
                method="GET",
                url=url,
                params=dict(kwargs.get("params") or {}),
                headers={"Accept": "application/json, application/pdf, */*"},
            )
        )
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(f"TJMG DSpace transport failed: {response.status.value}")
        self._last_http = {
            "http_status": response.status_code,
            "final_url": str(response.final_url or url),
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
        }
        status = int(response.status_code or 0)
        if status == 429:
            raise RateLimitDetectedError("TJMG DSpace returned HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TJMG DSpace returned HTTP {status}")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TJMG DSpace returned HTTP {status}")
        return response

    def _resolve_bitstream(self, item_url: str) -> str:
        bundles = self._request_json_url(f"{item_url}/bundles")
        for bundle in _embedded_list(bundles, "bundles"):
            if str(bundle.get("name", "")).upper() != "ORIGINAL":
                continue
            href = ((bundle.get("_links") or {}).get("bitstreams") or {}).get("href")
            if not href:
                continue
            bitstreams = self._request_json_url(str(href))
            for stream in _embedded_list(bitstreams, "bitstreams"):
                content = ((stream.get("_links") or {}).get("content") or {}).get("href")
                if content:
                    return str(content)
        raise SourceUnavailableError("TJMG DSpace item não possui bitstream ORIGINAL")

    def _request_json_url(self, url: str) -> dict[str, Any]:
        response = self._request(url)
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJMG DSpace retornou JSON inválido") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJMG DSpace retornou envelope inesperado")
        return data

    def _trace(
        self, query: JurisprudenceQuery, collection: str, params: dict[str, Any]
    ) -> SourceTrace:
        return SourceTrace(
            provider=self.name,
            endpoint=f"GET {SEARCH_PATH}",
            query={
                **params,
                "text": query.text,
                "number": query.number,
                "page": query.page,
                "collection": collection,
            },
            source_url=urljoin(self.base_url + "/", SEARCH_PATH.lstrip("/")),
            limitations=["A consulta combina três coleções públicas do repositório TJMG."],
            retrieval_status="ok",
            **self._last_http,
        )

    def _detail_trace(self, search_trace: SourceTrace, url: str) -> SourceTrace:
        return SourceTrace(
            provider=self.name,
            endpoint=f"GET {url}",
            query=search_trace.query,
            source_url=url,
            limitations=search_trace.limitations,
            retrieval_status="ok",
            transformations=["dspace_item_metadata", "pdf_original_bitstream"],
            **self._last_http,
        )


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TJMG DSpace exige termo, número ou frase exata")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TJMG DSpace suporta somente segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TJMG DSpace suporta somente instância de segundo grau")
    if query.branch and query.branch.casefold() not in {"state", "estadual"}:
        raise QueryRejectedError("TJMG DSpace pertence ao ramo estadual")
    if query.authority and query.authority.casefold() not in {
        "tjmg",
        "tribunal de justiça de minas gerais",
    }:
        raise QueryRejectedError("a autoridade solicitada não corresponde ao TJMG")


def _search_page(data: dict[str, Any]) -> dict[str, Any]:
    result = data.get("_embedded", {}).get("searchResult", {})
    if not isinstance(result, dict):
        raise ParserContractChangedError("TJMG DSpace não retornou searchResult")
    page = result.get("page") or {}
    total = page.get("totalElements") if isinstance(page, dict) else None
    try:
        total_value = int(total) if total is not None else None
    except (TypeError, ValueError):
        total_value = None
    objects = result.get("_embedded", {}).get("objects", [])
    items: list[dict[str, Any]] = []
    for obj in objects if isinstance(objects, list) else []:
        indexable = (
            obj.get("_embedded", {}).get("indexableObject", {}) if isinstance(obj, dict) else {}
        )
        if not isinstance(indexable, dict):
            continue
        item_id = indexable.get("id")
        if item_id and indexable.get("metadata"):
            items.append(
                {
                    "id": str(item_id),
                    "item_url": _item_url(indexable),
                    "metadata": indexable["metadata"],
                }
            )
    return {"total": total_value, "items": items}


def _parse_item(
    item: dict[str, Any], trace: SourceTrace, base_url: str
) -> JurisprudenceResult | None:
    metadata = item["metadata"]
    title = _first(metadata, "dc.title") or ""
    abstract = (
        _first(metadata, "dc.description.abstract") or _first(metadata, "dc.description") or ""
    )
    if not _CASE_RE.search(title) and not abstract.casefold().startswith("ementa"):
        return None
    case_number_match = _CASE_RE.search(title + " " + abstract)
    case_number = case_number_match.group(0) if case_number_match else None
    authors = _all(metadata, "dc.contributor.author")
    rapporteur = next((value for value in authors if "relator" in value.casefold()), None)
    judging_body = next(
        (
            value
            for value in authors
            if "tribunal" in value.casefold() or "câmara" in value.casefold()
        ),
        None,
    )
    issued = _first(metadata, "dc.date.issued")
    item_url = _item_url(item)
    result_id = f"tjmg-dspace-{item['id']}"
    collection = _collection_from_title(title)
    return JurisprudenceResult(
        id=result_id,
        source="tjmg_dspace_jurisprudencia",
        court="TJMG",
        type="acordao",
        number=case_number,
        summary=abstract,
        full_text=abstract,
        rapporteur=rapporteur,
        judging_body=judging_body,
        judgment_date=issued,
        publication_date=issued,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw={"item_id": item["id"], "title": title, "metadata": metadata, "item_url": item_url},
        case_class=title.split(" N", 1)[0].strip() or None,
        degree="second",
        instance="second",
        branch="state",
        authority="TJMG",
        collection=collection,
        document_type="acordao",
        source_origin="tjmg_digital_library",
        document_url=item_url,
    )


def _item_url(item: dict[str, Any]) -> str:
    href = ((item.get("_links") or {}).get("self") or {}).get("href")
    if href:
        return str(href)
    return f"https://bd.tjmg.jus.br/server/api/core/items/{item['id']}"


def _collection_from_title(title: str) -> str:
    upper = title.casefold()
    if "criminal" in upper or "habeas" in upper:
        return "CJSG_CRIMINAL"
    if "inconstitucionalidade" in upper or "órgão especial" in upper:
        return "CJSG_ORGAO_ESPECIAL"
    return "CJSG_CIVEL"


def _embedded_list(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get("_embedded", {}).get(key, [])
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _all(metadata: dict[str, Any], key: str) -> list[str]:
    values = metadata.get(key, [])
    return [
        str(item.get("value", ""))
        for item in values
        if isinstance(item, dict) and item.get("value")
    ]


def _first(metadata: dict[str, Any], key: str) -> str | None:
    values = _all(metadata, key)
    return values[0] if values else None


__all__ = ["TjmgDspaceJurisprudenciaProvider"]
