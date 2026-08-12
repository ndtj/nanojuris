from __future__ import annotations

import pytest

from nanojuris.canonical import result_to_canonical_decision
from nanojuris.client import NanoJurisClient
from nanojuris.errors import InvalidQueryError
from nanojuris.extraction import _status_to_access_status
from nanojuris.models import (
    AccessStatus,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
)


def test_canonical_mapper_preserves_access_evidence_and_date_meanings():
    result = JurisprudenceResult(
        id="decision-1",
        source="fixture",
        court="STJ",
        type="acordao",
        number="0001",
        summary="Ementa",
        updated_at="20/08/2026",
        publication_date="15/08/2026",
    )

    record = result_to_canonical_decision(result)

    assert record.access_status == AccessStatus.PARTIAL
    assert record.extraction_trace is not None
    assert record.extraction_trace.access_status == AccessStatus.PARTIAL
    assert record.judgment_date is None
    assert record.publication_date == "2026-08-15"
    assert record.publication_date_raw == "15/08/2026"
    assert record.source_updated_at == "2026-08-20"


@pytest.mark.parametrize("status", [400, 405, 409, 422])
def test_http_statuses_without_access_evidence_are_not_public(status):
    assert _status_to_access_status(status) == AccessStatus.PARTIAL


def test_query_rejects_unknown_filters_and_invalid_ranges():
    client = NanoJurisClient(providers=[])

    with pytest.raises(InvalidQueryError, match="desconhecido"):
        client.search("icms", source="missing", publised_from="2026-01-01")

    with pytest.raises(InvalidQueryError, match="page_size"):
        client.search("icms", source="missing", page_size=101)


class _FederatedProvider:
    def __init__(self, name: str, numbers: list[str]):
        self.name = name
        self.numbers = numbers

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        return SearchPage(
            source=self.name,
            total=len(self.numbers),
            start=1,
            end=len(self.numbers),
            page=query.page,
            page_size=query.page_size,
            results=[
                JurisprudenceResult(
                    id=f"{self.name}-{number}",
                    source=self.name,
                    court="STJ",
                    type="acordao",
                    number=number,
                    summary="ICMS ementa",
                    access_status=AccessStatus.PUBLIC,
                )
                for number in self.numbers
            ],
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name=self.name,
            source_url="https://example.test",
            category="court_jurisprudence",
            search_modes=["text"],
            supported_filters=["text"],
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
        )


def test_unified_search_applies_global_pagination_and_deduplication():
    client = NanoJurisClient(
        providers=[
            _FederatedProvider("a", ["1", "2"]),
            _FederatedProvider("b", ["2", "3"]),
        ]
    )

    payload = client.search_many("ICMS", page=2, page_size=2)

    assert payload["federated"] is True
    assert payload["total_available"] == 3
    assert payload["total_returned"] == 1
    assert payload["results"][0].case_number == "3"
    assert payload["collection_complete"] is False
    assert payload["sources_unknown"] == ["a", "b"]
    assert payload["source_completeness"]["a"]["complete"] is None
