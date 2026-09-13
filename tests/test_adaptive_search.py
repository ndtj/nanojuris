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
