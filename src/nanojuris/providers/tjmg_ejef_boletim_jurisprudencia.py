"""Public TJMG/EJEF Bulletin of Jurisprudence provider.

The EJEF publishes a curated collection of TJMG jurisprudence in the public
Digital Library.  This adapter is intentionally separate from the protected
TJMG search form and from the broader DSpace collection adapter so that the
curated scope, completeness limits and provenance remain visible.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from nanojuris.errors import ParserContractChangedError
from nanojuris.models import (
    AccessStatus,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.tjmg_dspace_jurisprudencia import (
    MAX_PAGE_SIZE,
    SEARCH_PATH,
    TjmgDspaceJurisprudenciaProvider,
    _all,
    _first,
    _parse_item,
    _search_page,
    _validate_query,
)

COLLECTION_UUID = "c4bd64ae-089d-446c-966f-2ba332a0cbf5"
COLLECTION_LABEL = "CJSG_EJEF_BOLETIM"


class TjmgEjefBoletimJurisprudenciaProvider(TjmgDspaceJurisprudenciaProvider):
    """Search the official, curated EJEF bulletin collection."""

    name = "tjmg_ejef_boletim_jurisprudencia"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        term = query.exact_phrase or query.text or query.number
        page_size = min(max(query.page_size, 1), MAX_PAGE_SIZE)
        remote_page = max(query.page - 1, 0)
        payload = {
            "query": term,
            "scope": COLLECTION_UUID,
            "size": page_size,
            "page": remote_page,
            "sort": "dc.date.issued,DESC",
        }
        data = self._request_json(payload)
        if not isinstance(data.get("_embedded", {}).get("searchResult"), dict):
            raise ParserContractChangedError("TJMG EJEF Boletim nao retornou searchResult")
        page_data = _search_page(data)
        trace = self._trace(query, COLLECTION_LABEL, payload)
        results = []
        for item in page_data["items"]:
            result = _parse_item(item, trace, self.base_url)
            if result is None:
                result = _parse_bulletin_item(item, trace)
            if result is None:
                continue
            result = replace(
                result,
                id=f"tjmg-ejef-boletim-{item['id']}",
                source=self.name,
                collection=COLLECTION_LABEL,
                source_origin="tjmg_ejef_boletim",
                raw={
                    **result.raw,
                    "collection_uuid": COLLECTION_UUID,
                    "curated": True,
                },
            )
            results.append(result)
            self._items[result.id] = {
                "item_url": item["item_url"],
                "metadata": item["metadata"],
                "trace": trace,
            }
        total = page_data["total"]
        total_known = total is not None
        total_value = total if total is not None else len(results)
        start = (query.page - 1) * page_size
        return SearchPage(
            source=self.name,
            total=total_value,
            start=start,
            end=start + len(results),
            page=query.page,
            page_size=page_size,
            results=results,
            source_trace=trace,
            pagination_mode="offset",
            is_complete=total_known and start + len(results) >= total_value,
            completeness_reason=(
                "totalElements informado pela colecao oficial"
                if total_known
                else "a colecao nao informou total autoritativo"
            ),
            ordering="publication_date_desc_then_id",
            filters_applied={
                "text": "native",
                "exact_phrase": "native_as_query",
                "number": "native_as_query",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
            },
            total_known=total_known,
            access_status=AccessStatus.PUBLIC,
        )

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
            source_url=f"{self.base_url}/collections/{COLLECTION_UUID}",
            limitations=[
                "Colecao curada de boletins; nao representa o acervo integral do TJMG.",
                "O formulario legado protegido por CAPTCHA nao e utilizado.",
            ],
            retrieval_status="ok",
            **self._last_http,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJMG/EJEF Boletim de Jurisprudencia",
            source_url=f"{self.base_url}/collections/{COLLECTION_UUID}",
            category="court_jurisprudence",
            search_modes=["text", "summary", "pagination", "date_range"],
            document_types=["acordao", "ementa", "boletim"],
            content_formats=["json", "pdf", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator="TJMG/EJEF curated bulletin collection",
            extracted_fields=[
                "uuid",
                "source_record_id",
                "title",
                "subject",
                "publication_date",
                "summary",
                "document_url",
                "collection",
                "degree",
                "instance",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /server/api/core/collections/{uuid}",
                "GET /server/api/discover/search/objects",
                "GET /server/api/core/items/{uuid}/bundles",
                "GET /server/api/core/bitstreams/{uuid}/content",
            ],
            supports_full_text=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            pagination_mode="offset",
            max_remote_page_size=MAX_PAGE_SIZE,
            completeness_contract="reported_collection_total_and_offset_window",
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
                "document_type",
                "decision_type",
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
                "authority": "validated_scope",
                "collection": "validated_scope",
                "page": "native",
            },
            ordering_modes=["publication_date_desc_then_id"],
            detail_modes=["lazy_document"],
            limitations=[
                "Colecao curada e historica de boletins, nao busca geral exaustiva.",
                "O PDF original pode ser image-only; OCR nao e presumido.",
            ],
            responsible_use=[
                "Usar chamadas publicas bounded e rate limit cooperativo.",
                "Preservar o escopo curado e SourceTrace.",
            ],
        )


__all__ = ["TjmgEjefBoletimJurisprudenciaProvider"]


def _parse_bulletin_item(item: dict[str, Any], trace: SourceTrace) -> JurisprudenceResult | None:
    """Normalize a bulletin whose DSpace metadata has no abstract field.

    EJEF bulletins expose their legal subjects and the official PDF as the
    searchable record.  They are valid curated second-degree evidence, but
    must not be mistaken for an individual case decision.  The result keeps
    the bulletin document type and preserves all source metadata in ``raw``.
    """

    metadata = item.get("metadata")
    if not isinstance(metadata, dict):
        return None
    title = _first(metadata, "dc.title") or ""
    if not title:
        return None
    subjects = _all(metadata, "dc.subject")
    author = _first(metadata, "dc.contributor.author")
    issued = _first(metadata, "dc.date.issued")
    item_url = str(item.get("item_url") or "")
    subject_text = "; ".join(subjects)
    summary = subject_text or title
    return JurisprudenceResult(
        id=f"tjmg-ejef-boletim-{item['id']}",
        source="tjmg_ejef_boletim_jurisprudencia",
        court="TJMG",
        type="boletim",
        summary=summary,
        full_text=summary,
        judging_body=author,
        judgment_date=issued,
        publication_date=issued,
        access_status=AccessStatus.PUBLIC,
        source_trace=trace,
        raw={"item_id": item["id"], "title": title, "metadata": metadata, "item_url": item_url},
        degree="second",
        instance="second",
        branch="state",
        authority="TJMG",
        collection=COLLECTION_LABEL,
        document_type="boletim",
        source_origin="tjmg_ejef_boletim",
        document_url=item_url,
    )
