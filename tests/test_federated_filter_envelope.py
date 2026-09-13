from __future__ import annotations

from nanojuris.contracts import ProviderOutcome, ProviderOutcomeStatus
from nanojuris.federated import (
    SearchIntent,
    merge_federated_pages,
    plan_federated_query,
    validate_federated_page,
)
from nanojuris.models import JurisprudenceResult, ProviderCapabilities, SearchPage


def test_federated_page_exposes_filter_application_plan() -> None:
    capability = ProviderCapabilities(
        source="tj",
        display_name="TJ",
        source_url="https://example.test",
        category="court_jurisprudence",
        supports_unified_search=True,
        supported_filters=["text"],
    )
    intent = SearchIntent(text="contrato", filters={"degree": "second"}, sources=("tj",))
    plan = plan_federated_query(intent, {"tj": capability})[0]
    page = SearchPage(
        source="tj",
        total=0,
        start=0,
        end=0,
        page=1,
        page_size=10,
        results=[],
        total_known=True,
        is_complete=True,
    )
    outcome = ProviderOutcome(
        provider="tj", operation="search", status=ProviderOutcomeStatus.EMPTY, complete=True
    )
    merged = merge_federated_pages({"tj": [page]}, outcomes={"tj": outcome}, plans={"tj": plan})
    payload = merged.to_dict()
    assert payload["provider_plans"]["tj"]["filter_support"]["degree"] == "unverified"
    assert "degree" in payload["provider_plans"]["tj"]["omitted_filters"]


def test_federated_planner_canonicalizes_common_aliases() -> None:
    capability = ProviderCapabilities(
        source="tj",
        display_name="TJ",
        source_url="https://example.test",
        category="court_jurisprudence",
        supports_unified_search=True,
        supported_filters=["courts"],
    )
    plan = plan_federated_query(
        SearchIntent(filters={"court_code": "TJSP"}, sources=("tj",)),
        {"tj": capability},
    )[0]
    assert plan.provider_query["courts"] == "TJSP"
    assert "canonicalized:court_code->courts" in plan.transformations


def test_federated_planner_keeps_validated_scope_out_of_remote_payload():
    capability = ProviderCapabilities(
        source="tj",
        display_name="TJ",
        source_url="https://example.test",
        category="court_jurisprudence",
        supports_unified_search=True,
        filter_semantics={"degree": "validated_scope"},
    )
    plan = plan_federated_query(
        SearchIntent(filters={"degree": "second"}, sources=("tj",)),
        {"tj": capability},
    )[0]
    assert "degree" not in plan.provider_query
    assert plan.filter_support["degree"].value == "validated_scope"
    assert "validated_scope:degree" in plan.transformations
    assert plan.omitted_filters == ()


def test_federated_page_validator_accepts_ordered_deduplicated_complete_page():
    page = SearchPage(
        source="tj",
        total=2,
        start=0,
        end=2,
        page=1,
        page_size=10,
        results=[
            JurisprudenceResult(
                id="new",
                source="tj",
                court="TJ",
                type="decision",
                summary="new",
                publication_date="2024-02-01",
            ),
            JurisprudenceResult(
                id="old",
                source="tj",
                court="TJ",
                type="decision",
                summary="old",
                publication_date="2024-01-01",
            ),
        ],
        total_known=True,
        is_complete=True,
    )
    outcome = ProviderOutcome(
        provider="tj", operation="search", status=ProviderOutcomeStatus.VALID, complete=True
    )
    merged = merge_federated_pages({"tj": [page]}, outcomes={"tj": outcome})

    assert validate_federated_page(merged) == ()


def test_federated_page_validator_surfaces_incomplete_envelope_reason():
    page = SearchPage(
        source="tj",
        total=0,
        start=0,
        end=0,
        page=1,
        page_size=10,
        results=[],
        total_known=False,
        is_complete=None,
    )
    merged = merge_federated_pages({"tj": [page]})

    assert "incomplete_page_missing_completeness_reason" not in validate_federated_page(merged)
    assert merged.complete is False
    assert merged.completeness_reason is not None
