from __future__ import annotations

import pytest

from nanojuris.canonical import result_to_canonical_decision
from nanojuris.client import NanoJurisClient
from nanojuris.errors import InvalidQueryError, UnsupportedQueryError
from nanojuris.extraction import _status_to_access_status
from nanojuris.models import (
    AccessStatus,
    ExtractionStatus,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
)
from nanojuris.routing import route_unified_sources


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
    assert record.extraction_status == ExtractionStatus.COMPLETE
    assert "canonical_mapping" in record.extraction_trace.transformations
    assert "publication_date_normalized_to_iso" in record.extraction_trace.transformations
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


def test_unified_router_warns_when_refinement_filters_are_not_declared():
    capability = ProviderCapabilities(
        source="fixture",
        display_name="Fixture",
        source_url="https://example.test",
        category="court_jurisprudence",
        supports_unified_search=True,
        supported_filters=["text"],
    )

    routed = route_unified_sources(
        selected_sources=["fixture"],
        capabilities={"fixture": capability},
        text="dano moral",
        filters={"published_from": "2021-01-01", "all_words": "transporte aereo"},
    )

    assert routed.searched == ["fixture"]
    assert routed.skipped == []
    assert {warning.reason for warning in routed.warnings} == {"filter_not_supported"}


def test_unified_router_skips_source_without_on_demand_full_text():
    capability = ProviderCapabilities(
        source="fixture",
        display_name="Fixture",
        source_url="https://example.test",
        category="court_jurisprudence",
        supports_unified_search=True,
        supported_filters=["text"],
        filter_semantics={"fetch_details": "unsupported"},
    )
    routed = route_unified_sources(
        selected_sources=["fixture"],
        capabilities={"fixture": capability},
        text="dano moral",
        filters={"fetch_details": True},
    )
    assert routed.searched == []
    assert routed.warnings == []
    assert routed.skipped[0].reason == "filter_not_supported"


def test_unified_router_skips_provider_when_required_scope_is_missing():
    capability = ProviderCapabilities(
        source="scoped_fixture",
        display_name="Scoped fixture",
        source_url="https://example.test",
        category="court_jurisprudence",
        supports_unified_search=True,
        supported_filters=["text", "authority"],
        filter_semantics={"text": "native", "authority": "required_scope"},
    )

    routed = route_unified_sources(
        selected_sources=["scoped_fixture"],
        capabilities={"scoped_fixture": capability},
        text="direito administrativo",
        filters={},
    )

    assert routed.searched == []
    assert routed.warnings == []
    assert routed.skipped[0].reason == "required_scope_missing"
    assert "authority" in routed.skipped[0].message

    scoped = route_unified_sources(
        selected_sources=["scoped_fixture"],
        capabilities={"scoped_fixture": capability},
        text="direito administrativo",
        filters={"authority": "TJSP"},
    )
    assert scoped.searched == ["scoped_fixture"]
    assert scoped.skipped == []


def test_single_source_search_rejects_undeclared_identifier_before_provider_call():
    class SpyProvider:
        name = "spy"
        called = False

        def search(self, _query: JurisprudenceQuery) -> SearchPage:
            self.called = True
            raise AssertionError("provider must not receive an unsupported identifier")

        def get_capabilities(self) -> ProviderCapabilities:
            return ProviderCapabilities(
                source=self.name,
                display_name="Spy",
                source_url="https://example.test",
                category="jurisprudence",
                supports_unified_search=True,
                supported_filters=["text"],
            )

    provider = SpyProvider()
    client = NanoJurisClient(providers=[provider])
    with pytest.raises(UnsupportedQueryError, match="number"):
        client.search("", source="spy", number="0000000-00.0000.0.00.0000")
    assert provider.called is False


def test_single_source_search_rejects_missing_required_scope_before_provider_call():
    class ScopedProvider:
        name = "scoped_spy"
        called = False

        def search(self, _query: JurisprudenceQuery) -> SearchPage:
            self.called = True
            raise AssertionError("provider must not receive an unscoped query")

        def get_capabilities(self) -> ProviderCapabilities:
            return ProviderCapabilities(
                source=self.name,
                display_name="Scoped spy",
                source_url="https://example.test",
                category="jurisprudence",
                supports_unified_search=False,
                supported_filters=["text", "authority"],
                filter_semantics={"text": "native", "authority": "required_scope"},
            )

    provider = ScopedProvider()
    client = NanoJurisClient(providers=[provider])
    with pytest.raises(UnsupportedQueryError, match="authority"):
        client.search("direito administrativo", source=provider.name)
    assert provider.called is False

    with pytest.raises(AssertionError):
        # The scoped call reaches the provider; this assertion documents that
        # the guard only rejects the missing precondition.
        client.search("direito administrativo", source=provider.name, authority="TRF4")


def test_unified_router_treats_empty_filter_declaration_as_unsupported_identifier():
    capability = ProviderCapabilities(
        source="fixture",
        display_name="Fixture",
        source_url="https://example.test",
        category="court_jurisprudence",
        supports_unified_search=True,
    )
    routed = route_unified_sources(
        selected_sources=["fixture"],
        capabilities={"fixture": capability},
        text="",
        filters={"number": "0000000-00.0000.0.00.0000"},
    )
    assert routed.searched == []
    assert routed.skipped[0].reason == "identifier_filter_not_supported"


def test_unified_router_warns_for_courts_and_types_without_contract():
    capability = ProviderCapabilities(
        source="fixture",
        display_name="Fixture",
        source_url="https://example.test",
        category="court_jurisprudence",
        supports_unified_search=True,
        supported_filters=["text"],
    )

    routed = route_unified_sources(
        selected_sources=["fixture"],
        capabilities={"fixture": capability},
        text="tributario",
        filters={"courts": ["TJSP"], "types": ["acordao"]},
    )

    assert routed.searched == ["fixture"]
    assert {warning.reason for warning in routed.warnings} == {"filter_not_supported"}
    assert {warning.message.split("'")[1] for warning in routed.warnings} == {"courts", "types"}


def test_unified_router_does_not_warn_for_a_source_that_was_skipped():
    capability = ProviderCapabilities(
        source="fixture",
        display_name="Fixture",
        source_url="https://example.test",
        category="court_jurisprudence",
        supports_unified_search=True,
        supported_filters=["text"],
    )

    routed = route_unified_sources(
        selected_sources=["fixture"],
        capabilities={"fixture": capability},
        text="0802253-46.2017.8.15.2003",
        filters={"number": "0802253-46.2017.8.15.2003", "all_words": "ICMS"},
    )

    assert routed.searched == []
    assert [skip.reason for skip in routed.skipped] == ["identifier_filter_not_supported"]
    assert routed.warnings == []


def test_unified_search_marks_collection_incomplete_for_filter_warnings():
    client = NanoJurisClient(providers=[_FederatedProvider("fixture", ["1"])])

    payload = client.search_many(
        "ICMS",
        sources=["fixture"],
        published_from="2021-01-01",
    )

    assert payload["routing_warnings"][0]["reason"] == "filter_not_supported"
    assert payload["collection_complete"] is False


def test_single_source_search_exposes_missing_filter_disposition():
    class Provider:
        name = "filter_boundary"

        def search(self, query: JurisprudenceQuery) -> SearchPage:
            return SearchPage(
                source=self.name,
                total=0,
                start=0,
                end=0,
                page=query.page,
                page_size=query.page_size,
                results=[],
                is_complete=True,
                total_known=True,
            )

        def get_capabilities(self) -> ProviderCapabilities:
            return ProviderCapabilities(
                source=self.name,
                display_name="Filter boundary",
                source_url="https://example.test",
                category="jurisprudence",
                supported_filters=["text"],
                filter_semantics={"text": "native", "published_from": "unsupported"},
            )

    page = NanoJurisClient(providers=[Provider()]).search(
        "responsabilidade", source="filter_boundary", published_from="2026-01-01"
    )
    assert page.filters_applied == {
        "published_from": "unsupported",
        "text": "native",
    }


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


class _FilterCaptureProvider:
    name = "tre_filter_capture"

    def __init__(self) -> None:
        self.query: JurisprudenceQuery | None = None

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        self.query = query
        return SearchPage(
            source=self.name,
            total=0,
            start=0,
            end=0,
            page=query.page,
            page_size=query.page_size,
            results=[],
            is_complete=True,
            total_known=True,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        tre_filters = [
            "text",
            "election_year",
            "observations",
            "tags",
            "municipality",
            "publication_source",
            "publication_number",
            "publication_volume",
            "uf",
        ]
        return ProviderCapabilities(
            source=self.name,
            display_name=self.name,
            source_url="https://example.test",
            category="court_jurisprudence",
            supports_unified_search=True,
            supported_filters=tre_filters,
            filter_semantics={name: "native" for name in tre_filters},
        )


def test_client_forwards_tre_structured_filters_and_portuguese_aliases() -> None:
    provider = _FilterCaptureProvider()
    page = NanoJurisClient(providers=[provider]).search(
        "eleicao",
        source=provider.name,
        ano_eleicao="2022",
        observacoes="urna",
        etiquetas="propaganda",
        municipio="Sao Paulo",
        fonte_publicacao="DJE",
        numero_publicacao="12",
        volume_publicacao="3",
        uf="SP",
    )

    assert page.is_explicit_empty
    assert provider.query is not None
    assert provider.query.election_year == "2022"
    assert provider.query.observations == "urna"
    assert provider.query.tags == "propaganda"
    assert provider.query.municipality == "Sao Paulo"
    assert provider.query.publication_source == "DJE"
    assert provider.query.publication_number == "12"
    assert provider.query.publication_volume == "3"
    assert provider.query.uf == "SP"
    assert set(page.filters_applied) >= {
        "election_year",
        "observations",
        "tags",
        "municipality",
        "publication_source",
        "publication_number",
        "publication_volume",
        "uf",
    }


def test_adaptive_plan_canonicalizes_tre_filter_aliases() -> None:
    provider = _FilterCaptureProvider()
    payload = NanoJurisClient(providers=[provider]).search_many(
        "eleicao",
        sources=[provider.name],
        mode="selected",
        ano_eleicao="2022",
    )

    plan = payload["search_plan"]["provider_plans"][provider.name]
    assert plan["provider_query"]["election_year"] == "2022"
    assert "ano_eleicao" not in plan["provider_query"]


class _PagedProvider(_FederatedProvider):
    def __init__(self, name: str, numbers: list[str]):
        super().__init__(name, numbers)
        self.page_requests: list[tuple[int, int]] = []

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        self.page_requests.append((query.page, query.page_size))
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        page_numbers = self.numbers[start:end]
        return SearchPage(
            source=self.name,
            total=len(self.numbers),
            start=start + 1 if page_numbers else 0,
            end=start + len(page_numbers),
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
                for number in page_numbers
            ],
            is_complete=end >= len(self.numbers),
            completeness_reason="fixture paginada",
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
    assert payload["total_available"] == 4
    assert payload["total_returned"] == 2
    assert payload["results"][0].case_number == "2"
    assert len(payload["collected_results"]) == 4
    assert {item.case_number for item in payload["collected_results"]} == {"1", "2", "3"}
    assert payload["collection_complete"] is False
    assert payload["has_more"] is False
    assert payload["previous_page"] == 1
    assert payload["observed_total_pages"] == 2
    assert payload["sources_unknown"] == ["a", "b"]
    assert payload["source_completeness"]["a"]["complete"] is None


def test_unified_search_fetches_incremental_source_pages_after_first_window():
    provider = _PagedProvider("paged", [str(index) for index in range(1, 251)])
    client = NanoJurisClient(providers=[provider])

    payload = client.search_many("ICMS", sources=["paged"], page=11, page_size=10)

    assert payload["total_returned"] == 10
    assert payload["has_more"] is True
    assert payload["observed_total_pages"] == 20
    assert payload["source_completeness"]["paged"]["pages_fetched"] == 2
    assert provider.page_requests == [(1, 100), (2, 100)]


@pytest.mark.parametrize(
    ("start", "end", "message"),
    [
        ("2026-08-20", "2026-08-19", "published_from"),
        ("20/08/2026", "19/08/2026", "updated_from"),
    ],
)
def test_query_rejects_inverted_date_ranges(start, end, message):
    kwargs = {
        "published_from": start,
        "published_to": end,
    }
    if message == "updated_from":
        kwargs = {"updated_from": start, "updated_to": end}

    with pytest.raises(ValueError, match=message):
        JurisprudenceQuery(**kwargs)


def test_canonical_mapper_treats_full_text_as_complete_primary_content():
    result = JurisprudenceResult(
        id="decision-full-text",
        source="fixture",
        court="TJDFT",
        type="acordao",
        full_text="Inteiro teor da decisao",
    )

    record = result_to_canonical_decision(result)

    assert record.extraction_status == ExtractionStatus.COMPLETE
    assert record.extraction_trace is not None
    assert "extraction_status_downgraded_to_partial" not in record.extraction_trace.transformations
