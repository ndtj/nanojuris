from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.contracts import (
    FilterContract,
    FilterSupport,
    ProviderOutcome,
    ProviderOutcomeStatus,
    filter_contracts_for,
)
from nanojuris.contracts_adapter import (
    classify_error,
    normalize_filters_applied,
    outcome_from_error,
)
from nanojuris.errors import AccessControlRequiredError, RateLimitDetectedError
from nanojuris.federated import (
    FederatedCursor,
    SearchIntent,
    merge_federated_pages,
    plan_federated_query,
)
from nanojuris.models import (
    ExtractionStatus,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)


def _page(
    *,
    results: list[JurisprudenceResult],
    source: str = "fixture",
    page: int = 1,
    complete: bool | None = True,
) -> SearchPage:
    return SearchPage(
        source=source,
        total=len(results),
        start=0,
        end=len(results),
        page=page,
        page_size=10,
        results=results,
        is_complete=complete,
        completeness_reason=None if complete else "bounded source page",
    )


def _result(
    *, id: str = "fixture-1", source: str = "fixture", publication_date: str | None = None
) -> JurisprudenceResult:
    return JurisprudenceResult(
        id=id,
        source=source,
        court="STF",
        type="decision",
        summary="Ementa de teste",
        publication_date=publication_date,
    )


def test_capabilities_keep_legacy_lists_and_expose_explicit_status() -> None:
    capabilities = ProviderCapabilities(
        source="fixture",
        display_name="Fixture",
        source_url="https://example.test",
        category="jurisprudence",
        supported_filters=["court"],
        unsupported_filters=["party_name"],
        filter_semantics={"published_from": "translated", "broken": "future"},
    )

    assert capabilities.filter_status("court") == "native"
    assert capabilities.filter_status("party_name") == "unsupported"
    assert capabilities.filter_status("published_from") == "translated"
    assert capabilities.filter_status("broken") == "unverified"
    assert capabilities.filter_status("unknown") == "unverified"


def test_filter_contracts_are_deterministic_and_explicit_wins() -> None:
    contracts = filter_contracts_for(
        supported=["court", "court"],
        unsupported=["party_name"],
        explicit={
            "court": FilterContract(
                name="court",
                support=FilterSupport.LOCAL_POSTFILTER,
                evidence="fixture",
            ),
            "published_from": "translated",
        },
    )

    assert list(contracts) == ["court", "party_name", "published_from"]
    assert contracts["court"].support is FilterSupport.LOCAL_POSTFILTER
    assert contracts["published_from"].support is FilterSupport.TRANSLATED


def test_filter_contract_rejects_mismatched_explicit_key() -> None:
    with pytest.raises(ValueError, match="key and contract name differ"):
        filter_contracts_for(
            explicit={"court": FilterContract(name="different")},
        )


def test_provider_outcome_distinguishes_valid_empty_and_partial() -> None:
    valid = ProviderOutcome.from_page(_page(results=[_result()]))
    empty = ProviderOutcome.from_page(_page(results=[]))
    partial = ProviderOutcome.from_page(_page(results=[_result()], complete=False))

    assert valid.status is ProviderOutcomeStatus.VALID
    assert valid.returned == 1
    assert empty.status is ProviderOutcomeStatus.EMPTY
    assert partial.status is ProviderOutcomeStatus.PARTIAL
    assert partial.complete is False


def test_provider_outcome_does_not_promote_unknown_empty_page() -> None:
    unknown = ProviderOutcome.from_page(_page(results=[], complete=None))

    assert unknown.status is ProviderOutcomeStatus.EMPTY_UNCONFIRMED
    assert unknown.returned == 0
    assert unknown.complete is None


def test_provider_outcome_distinguishes_schema_invalid_from_parser_failure() -> None:
    page = _page(results=[])
    page.extraction_status = ExtractionStatus.PARSER_CONTRACT_CHANGED

    outcome = ProviderOutcome.from_page(page)

    assert outcome.status is ProviderOutcomeStatus.SCHEMA_INVALID


def test_provider_outcome_redacts_diagnostic_details() -> None:
    outcome = ProviderOutcome(
        provider="fixture",
        operation="search",
        status=ProviderOutcomeStatus.UNAVAILABLE,
        error_type="TimeoutError",
        message=("https://user:secret@example.test/search?token=abc contact admin@example.test"),
    )

    payload = outcome.to_dict()
    assert "secret" not in payload["message"]
    assert "admin@example.test" not in payload["message"]
    assert "https://example.test/search" in payload["message"]


def test_search_page_additive_cursor_metadata_serializes() -> None:
    page = _page(results=[])
    page.cursor = "next-1"
    page.ordering = "published_desc"
    page.filters_applied = {"court": "STF"}

    assert page.to_dict()["cursor"] == "next-1"
    assert page.to_dict()["ordering"] == "published_desc"
    assert page.to_dict()["filters_applied"] == {"court": "STF"}


@pytest.mark.parametrize(
    ("error", "status", "retryable"),
    [
        (AccessControlRequiredError("login required"), ProviderOutcomeStatus.BLOCKED, False),
        (RateLimitDetectedError("retry later"), ProviderOutcomeStatus.RATE_LIMITED, True),
        (TimeoutError("source timed out"), ProviderOutcomeStatus.TIMEOUT, True),
    ],
)
def test_legacy_error_adapter_preserves_failure_semantics(
    error: BaseException,
    status: ProviderOutcomeStatus,
    retryable: bool,
) -> None:
    assert classify_error(error) == (status, retryable)
    outcome = outcome_from_error("fixture", error)
    assert outcome.status is status
    assert outcome.retryable is retryable
    assert outcome.returned == 0


def test_filter_metadata_adapter_is_sorted_and_stringified() -> None:
    assert normalize_filters_applied({"page": 2, "court": "STF"}) == {
        "court": "STF",
        "page": "2",
    }


def test_contract_schema_matches_public_outcome_vocabulary() -> None:
    schema_path = Path(__file__).parents[1] / "docs" / "provider-contract-v2.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["required"] == ["provider", "operation", "status", "returned", "retryable"]
    assert set(schema["properties"]["status"]["enum"]) == {
        status.value for status in ProviderOutcomeStatus
    }


def test_federated_planner_never_sends_unsupported_or_unknown_filters() -> None:
    capabilities = {
        "native": ProviderCapabilities(
            source="native",
            display_name="Native",
            source_url="https://example.test/native",
            category="court_jurisprudence",
            supports_unified_search=True,
            supported_filters=["court"],
        ),
        "local": ProviderCapabilities(
            source="local",
            display_name="Local",
            source_url="https://example.test/local",
            category="court_jurisprudence",
            supports_unified_search=True,
            filter_semantics={"published_from": "local_postfilter"},
        ),
    }
    intent = SearchIntent(
        text="dano moral",
        filters={"court": "STF", "published_from": "2024-01-01", "unknown": "x"},
        sources=("native", "local", "missing"),
    )

    plans = plan_federated_query(intent, capabilities)

    assert [plan.source for plan in plans] == ["native", "local", "missing"]
    assert plans[0].provider_query == {"text": "dano moral", "court": "STF"}
    assert plans[0].omitted_filters == ("published_from", "unknown")
    assert plans[1].local_filters == {"published_from": "2024-01-01"}
    assert "unknown" in plans[2].omitted_filters


def test_federated_cursor_is_versioned_and_bound_to_intent() -> None:
    intent = SearchIntent(text="precedente", sources=("stf_juris",))
    cursor = FederatedCursor(intent.fingerprint(), {"stf_juris": 2})

    restored = FederatedCursor.decode(cursor.encode())

    assert restored == cursor
    assert restored.matches(intent)
    assert not restored.matches(SearchIntent(text="outro", sources=("stf_juris",)))
    with pytest.raises(ValueError, match="invalid federated cursor"):
        FederatedCursor.decode("not-a-cursor")


def test_federated_merge_deduplicates_identity_and_surfaces_partial_source() -> None:
    first = _result(id="a", source="source-a", publication_date="2024-01-01")
    second = _result(id="b", source="source-a", publication_date="2025-01-01")
    duplicate = _result(id="a", source="source-a", publication_date="2024-01-01")
    other = _result(id="c", source="source-b", publication_date="2026-01-01")

    merged = merge_federated_pages(
        {
            "source-a": [
                _page(results=[first, second], source="source-a"),
                _page(results=[duplicate], source="source-a", page=2),
            ],
            "source-b": [_page(results=[other], source="source-b", complete=False)],
        },
        ordering="published_desc",
    )

    assert [record.id for record in merged.results] == ["c", "b", "a"]
    assert merged.raw_result_count == 4
    assert merged.duplicate_count == 1
    assert merged.complete is False
    assert merged.completeness_reason == "source_incomplete:source-b"
    assert merged.source_outcomes["source-a"].complete is True
    assert merged.source_outcomes["source-b"].status is ProviderOutcomeStatus.PARTIAL
    assert merged.to_dict()["source_outcomes"]["source-b"]["status"] == "partial"


def test_federated_merge_caps_results_and_rejects_native_relevance_ordering() -> None:
    pages = {
        "source-a": [
            _page(
                source="source-a",
                results=[
                    _result(id="a", source="source-a", publication_date="2026-01-01"),
                    _result(id="b", source="source-a", publication_date="2025-01-01"),
                ],
            )
        ]
    }

    merged = merge_federated_pages(pages, max_results=1)

    assert [record.id for record in merged.results] == ["a"]
    assert merged.complete is False
    assert merged.completeness_reason == "max_results"
    with pytest.raises(ValueError, match="ordering"):
        merge_federated_pages(pages, ordering="relevance")


def test_federated_merge_rejects_misattributed_page_source() -> None:
    with pytest.raises(ValueError, match="diverges"):
        merge_federated_pages({"source-a": [_page(source="source-b", results=[_result()])]})


def test_federated_merge_preserves_transport_failure_status() -> None:
    page = _page(results=[], source="source-a")
    page.source_trace = SourceTrace(
        provider="source-a",
        endpoint="https://example.test/search",
        retrieval_status="timeout",
    )
    merged = merge_federated_pages({"source-a": [page]})
    outcome = merged.source_outcomes["source-a"]
    assert outcome.status is ProviderOutcomeStatus.TIMEOUT
    assert outcome.retryable is True


def test_federated_merge_preserves_unknown_empty_status() -> None:
    page = _page(results=[], source="source-a", complete=None)

    merged = merge_federated_pages({"source-a": [page]})

    outcome = merged.source_outcomes["source-a"]
    assert outcome.status is ProviderOutcomeStatus.EMPTY_UNCONFIRMED
    assert outcome.complete is None
    assert merged.complete is False
