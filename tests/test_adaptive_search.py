from __future__ import annotations

import pytest

from nanojuris.adaptive_search import (
    GLOBAL_CANDIDATE_BUDGET,
    MAX_ADAPTIVE_SOURCES,
    SearchMode,
    plan_live_search,
)
from nanojuris.models import ProviderCapabilities


def _capability(source: str, *, category: str = "court_jurisprudence") -> ProviderCapabilities:
    return ProviderCapabilities(
        source=source,
        display_name=source,
        source_url=f"https://{source}.example",
        category=category,
        supports_unified_search=True,
        supports_full_text=source.endswith("_full"),
        full_text_access="document_link" if source.endswith("_full") else "unknown",
        pagination_mode="page",
        supported_filters=["degree", "document_type"],
        filter_semantics={"degree": "native", "document_type": "native"},
    )


def test_adaptive_plan_is_bounded_and_forms_three_stable_waves() -> None:
    names = [f"tj{index:02d}" for index in range(15)]
    capabilities = {name: _capability(name) for name in names}

    plan = plan_live_search(
        text="divórcio",
        filters={"degree": "second"},
        capabilities=capabilities,
    )

    assert plan.mode is SearchMode.ADAPTIVE
    assert len(plan.sources) == MAX_ADAPTIVE_SOURCES
    assert [source for wave in plan.waves for source in wave.sources] == list(plan.sources)
    assert len(plan.waves) == 3
    assert plan.global_candidate_budget == GLOBAL_CANDIDATE_BUDGET
    assert len(plan.sources) * plan.per_source_budget == GLOBAL_CANDIDATE_BUDGET
    assert plan.provider_plans[plan.sources[0]].provider_query["degree"] == "second"
    assert (
        plan.plan_id
        == plan_live_search(
            text="divórcio",
            filters={"degree": "second"},
            capabilities=capabilities,
        ).plan_id
    )


def test_selected_plan_preserves_explicit_missing_source_for_observable_failure() -> None:
    plan = plan_live_search(
        text="dano moral",
        capabilities={"tjsp": _capability("tjsp")},
        mode="selected",
        sources=["missing", "tjsp", "missing"],
    )

    assert plan.sources == ("missing", "tjsp")
    assert "missing" in plan.provider_plans
    assert plan.omitted_sources == ()


def test_adaptive_plan_respects_explicit_scope_before_diversifying() -> None:
    capabilities = {
        **{f"tj{index:02d}": _capability(f"tj{index:02d}") for index in range(15)},
        "restricted": ProviderCapabilities(
            source="restricted",
            display_name="restricted",
            source_url="https://restricted.example",
            category="court_jurisprudence",
            supports_unified_search=True,
            access_statuses=["login_required"],
        ),
    }

    plan = plan_live_search(
        capabilities=capabilities,
        mode=SearchMode.ADAPTIVE,
        sources=["tj09", "tj10", "tj11", "restricted"],
    )

    assert set(plan.sources) <= {"tj09", "tj10", "tj11"}
    assert set(plan.omitted_sources) == {
        "tj00",
        "tj01",
        "tj02",
        "tj03",
        "tj04",
        "tj05",
        "tj06",
        "tj07",
        "tj08",
        "tj12",
        "tj13",
        "tj14",
        "restricted",
    }


def test_all_plan_respects_explicit_scope_without_repeating_full_federation() -> None:
    capabilities = {f"tj{index:02d}": _capability(f"tj{index:02d}") for index in range(6)}

    plan = plan_live_search(
        capabilities=capabilities,
        mode=SearchMode.ALL,
        sources=["tj04", "tj01"],
    )

    assert plan.sources == ("tj01", "tj04")
    assert set(plan.omitted_sources) == {"tj00", "tj02", "tj03", "tj05"}


def test_all_mode_can_include_context_only_when_explicit() -> None:
    capabilities = {
        "court": _capability("court"),
        "context": _capability("context", category="specialized_context"),
    }

    adaptive = plan_live_search(capabilities=capabilities)
    all_mode = plan_live_search(capabilities=capabilities, mode=SearchMode.ALL)

    assert "context" not in adaptive.sources
    assert "context" in all_mode.sources


def test_invalid_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="mode must be"):
        plan_live_search(capabilities={}, mode="everything")
