from __future__ import annotations

import pytest

from nanojuris.canonical import result_to_canonical_decision
from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.contracts import ProviderOutcome, ProviderOutcomeStatus
from nanojuris.models import (
    DecisionBundle,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.store import SQLiteStore


def _result(identifier: str, *, number: str = "") -> JurisprudenceResult:
    return JurisprudenceResult(
        id=identifier,
        source="fixture_quality",
        court="TJSP",
        type="decision",
        number=number or None,
        summary="Ementa pública de teste",
        case_class="Apelação Cível",
        judging_body="2ª Câmara",
        degree="second",
        branch="state",
        collection="CJSG",
        source_trace=SourceTrace(provider="fixture_quality", endpoint="/search"),
    )


class UnknownTotalProvider(JurisprudenceProvider):
    name = "fixture_quality"

    def __init__(self) -> None:
        self.calls: list[int] = []

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="Fixture quality",
            source_url="https://example.test",
            category="jurisprudence",
            supports_unified_search=True,
            supported_filters=["text"],
        )

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        self.calls.append(query.page)
        if query.page == 1:
            return SearchPage(
                source=self.name,
                total=0,
                start=0,
                end=1,
                page=1,
                page_size=1,
                results=[_result("first")],
                is_complete=None,
                completeness_reason="remote total unavailable",
                total_known=False,
            )
        return SearchPage(
            source=self.name,
            total=0,
            start=1,
            end=1,
            page=query.page,
            page_size=1,
            results=[],
            is_complete=True,
            total_known=True,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(precedent_id=precedent_id, source=self.name)


def test_search_page_distinguishes_unknown_total_from_explicit_empty() -> None:
    unknown = SearchPage(
        source="x",
        total=0,
        start=0,
        end=0,
        page=1,
        page_size=10,
        results=[],
    )
    explicit = SearchPage(
        source="x",
        total=0,
        start=0,
        end=0,
        page=1,
        page_size=10,
        results=[],
        total_known=True,
        is_complete=True,
    )
    assert unknown.effective_total is None
    assert not unknown.is_explicit_empty
    assert explicit.effective_total == 0
    assert explicit.is_explicit_empty


def test_federation_does_not_stop_on_ambiguous_zero_total() -> None:
    provider = UnknownTotalProvider()
    payload = NanoJurisClient(providers=[provider]).search_many(
        "responsabilidade", sources=[provider.name], page_size=2
    )
    assert provider.calls == [1, 2]
    assert payload["total_returned"] == 1
    assert payload["source_total_known"][provider.name] is True


def test_federation_stops_repeated_source_page_without_marking_complete() -> None:
    class RepeatingProvider(UnknownTotalProvider):
        def search(self, query: JurisprudenceQuery) -> SearchPage:
            return SearchPage(
                source=self.name,
                total=0,
                start=0,
                end=1,
                page=query.page,
                page_size=query.page_size,
                results=[_result("repeated")],
                is_complete=None,
                total_known=False,
            )

    provider = RepeatingProvider()
    payload = NanoJurisClient(providers=[provider]).search_many(
        "responsabilidade", sources=[provider.name], page_size=3
    )
    completeness = payload["source_completeness"][provider.name]
    assert completeness["returned"] == 1
    assert completeness["pages_fetched"] == 2
    assert completeness["complete"] is None
    assert "repetiu" in completeness["reason"]
    assert payload["total_returned"] == 1
    assert payload["source_totals"][provider.name] is None
    assert payload["source_completeness"][provider.name]["reported_total"] is None


def test_federation_applies_per_source_page_budget_without_false_completion() -> None:
    class UnboundedProvider(UnknownTotalProvider):
        def search(self, query: JurisprudenceQuery) -> SearchPage:
            return SearchPage(
                source=self.name,
                total=0,
                start=query.page,
                end=query.page,
                page=query.page,
                page_size=query.page_size,
                results=[_result(f"page-{query.page}")],
                is_complete=None,
                total_known=False,
            )

    provider = UnboundedProvider()
    client = NanoJurisClient(
        config=NanoJurisConfig(unified_max_pages=2, rate_limit_interval=0),
        providers=[provider],
    )
    payload = client.search_many("responsabilidade", sources=[provider.name], page_size=5)
    completeness = payload["source_completeness"][provider.name]
    assert completeness["pages_fetched"] == 2
    assert completeness["returned"] == 2
    assert completeness["complete"] is None
    assert "limite federado" in completeness["reason"]


def test_federation_deduplicates_cross_source_cnj_decisions() -> None:
    first = _result("source-a", number="0000001-02.2024.8.26.0001")
    first.source = "source-a"
    second = JurisprudenceResult(
        id="source-b",
        source="other_source",
        court="TJSP",
        type="decision",
        number="0000001-02.2024.8.26.0001",
        summary="Ementa pública de teste",
        judgment_date="2024-02-01",
    )
    first.judgment_date = "2024-02-01"

    class StaticProvider(UnknownTotalProvider):
        def __init__(self, name: str, item: JurisprudenceResult) -> None:
            self.name = name
            self.item = item
            self.calls = []

        def get_capabilities(self) -> ProviderCapabilities:
            capabilities = super().get_capabilities()
            capabilities.source = self.name
            return capabilities

        def search(self, query: JurisprudenceQuery) -> SearchPage:
            return SearchPage(
                source=self.name,
                total=1,
                start=0,
                end=1,
                page=query.page,
                page_size=query.page_size,
                results=[self.item] if query.page == 1 else [],
                is_complete=True,
                total_known=True,
            )

    payload = NanoJurisClient(
        providers=[StaticProvider("source-a", first), StaticProvider("other_source", second)]
    ).search_many(
        "responsabilidade",
        sources=["source-a", "other_source"],
        page_size=2,
    )
    assert payload["deduplicated_total"] == 1


def test_canonical_semantic_dimensions_roundtrip_to_sqlite() -> None:
    result = _result(
        "decision-1",
        number="0000001-02.2024.8.26.0001",
    )
    result.judgment_date = "2024-02-01"
    decision = result_to_canonical_decision(result)
    assert decision.case_class == "Apelação Cível"
    assert decision.judging_body == "2ª Câmara"
    assert decision.degree == "second"
    assert decision.collection == "CJSG"
    assert decision.field_provenance["case_class"]["path"] == "result.case_class"
    with SQLiteStore(":memory:") as store:
        store.save(decision)
        rows = store.query_records(
            degree="second",
            case_class="Apelação Cível",
            collection="CJSG",
            judgment_date_from="2024-01-01",
            judgment_date_to="2024-12-31",
        )
        assert [row["id"] for row in rows] == ["decision-1"]
        columns = {
            str(row["name"])
            for row in store.connection.execute("PRAGMA table_info(canonical_records)")
        }
        assert {"degree", "collection", "judgment_date", "access_status"}.issubset(columns)


def test_query_exposes_canonical_refinements_without_breaking_v1() -> None:
    query = JurisprudenceQuery(
        text="ICMS",
        case_class="Apelação Cível",
        judging_body="2ª Câmara",
        degree="second",
        branch="state",
        collection="CJSG",
    )
    payload = query.to_dict()
    assert payload["case_class"] == "Apelação Cível"
    assert payload["degree"] == "second"
    assert payload["collection"] == "CJSG"


def test_sqlite_full_text_projection_is_searchable_and_bounded() -> None:
    result = _result("decision-fts")
    decision = result_to_canonical_decision(result)
    with SQLiteStore(":memory:") as store:
        store.save(decision)
        rows = store.search_full_text("Ementa", kind="decision")
        assert [row["id"] for row in rows] == ["decision-fts"]
        assert store.search_full_text("", kind="decision") == []
        with pytest.raises(ValueError, match="FTS"):
            store.search_full_text('title:"unterminated', kind="decision")


def test_provider_outcome_never_collapses_transport_failure_into_empty() -> None:
    trace = SourceTrace(
        provider="fixture_quality",
        endpoint="https://example.test/juris",
        retrieval_status="timeout",
    )
    outcome = ProviderOutcome.from_page(
        SearchPage(
            source="fixture_quality",
            total=0,
            start=0,
            end=0,
            page=1,
            page_size=10,
            results=[],
            source_trace=trace,
        )
    )
    assert outcome.status is ProviderOutcomeStatus.TIMEOUT
    assert outcome.retryable is True
