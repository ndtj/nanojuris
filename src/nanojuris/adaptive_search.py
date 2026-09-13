"""Deterministic source planning for bounded live federated search.

The planner chooses sources only from the capabilities supplied by the caller.
It never turns a missing capability into an assertion of support, and it never
uses provider-local native scores to choose a source. Network execution stays
in ``NanoJurisClient``; this module only creates an auditable plan.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from nanojuris.federated import ProviderQueryPlan, SearchIntent, plan_federated_query
from nanojuris.models import ProviderCapabilities
from nanojuris.routing import JURISPRUDENCE_CATEGORIES

MAX_ADAPTIVE_SOURCES = 12
MIN_ADAPTIVE_SOURCES = 8
PER_SOURCE_CANDIDATE_BUDGET = 20
GLOBAL_CANDIDATE_BUDGET = 240
DEFAULT_SOURCE_TIMEOUT_SECONDS = 8.0
DEFAULT_WAVE_TIMEOUT_SECONDS = 12.0
PLANNER_VERSION = "adaptive-live-v1"


class SearchMode(str, Enum):
    """Explicit source-selection modes exposed by the live API."""

    ADAPTIVE = "adaptive"
    SELECTED = "selected"
    ALL = "all"


@dataclass(frozen=True, slots=True)
class SourceWave:
    """A bounded execution wave in deterministic source order."""

    number: int
    sources: tuple[str, ...]
    deadline_seconds: float = DEFAULT_WAVE_TIMEOUT_SECONDS
    candidate_budget: int = PER_SOURCE_CANDIDATE_BUDGET

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("wave number must be positive")
        if self.deadline_seconds <= 0:
            raise ValueError("wave deadline must be positive")
        if self.candidate_budget < 1:
            raise ValueError("wave candidate budget must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "sources": list(self.sources),
            "deadline_seconds": self.deadline_seconds,
            "candidate_budget": self.candidate_budget,
        }


@dataclass(frozen=True, slots=True)
class SearchPlan:
    """Complete, serializable execution plan for one federated search."""

    plan_id: str
    planner_version: str
    mode: SearchMode
    intent: SearchIntent
    sources: tuple[str, ...]
    waves: tuple[SourceWave, ...]
    provider_plans: dict[str, ProviderQueryPlan]
    per_source_budget: int = PER_SOURCE_CANDIDATE_BUDGET
    global_candidate_budget: int = GLOBAL_CANDIDATE_BUDGET
    source_timeout_seconds: float = DEFAULT_SOURCE_TIMEOUT_SECONDS
    wave_timeout_seconds: float = DEFAULT_WAVE_TIMEOUT_SECONDS
    ranking_version: str = "legacy"
    omitted_sources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.plan_id or not self.planner_version:
            raise ValueError("plan identity must not be empty")
        if self.per_source_budget < 1 or self.global_candidate_budget < 1:
            raise ValueError("candidate budgets must be positive")
        if self.source_timeout_seconds <= 0 or self.wave_timeout_seconds <= 0:
            raise ValueError("timeouts must be positive")
        if self.mode is SearchMode.ADAPTIVE and len(self.sources) > MAX_ADAPTIVE_SOURCES:
            raise ValueError("a live plan cannot contain more than 12 sources")
        if len(self.waves) > 3:
            raise ValueError("a live plan cannot contain more than three waves")

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "planner_version": self.planner_version,
            "mode": self.mode.value,
            "intent": {
                "text": self.intent.text,
                "filters": dict(self.intent.filters),
                "sources": list(self.intent.sources),
                "ordering": self.intent.ordering,
            },
            "sources": list(self.sources),
            "waves": [wave.to_dict() for wave in self.waves],
            "provider_plans": {
                source: plan.to_dict() for source, plan in self.provider_plans.items()
            },
            "per_source_budget": self.per_source_budget,
            "global_candidate_budget": self.global_candidate_budget,
            "source_timeout_seconds": self.source_timeout_seconds,
            "wave_timeout_seconds": self.wave_timeout_seconds,
            "ranking_version": self.ranking_version,
            "omitted_sources": list(self.omitted_sources),
        }


def plan_live_search(
    *,
    text: str = "",
    filters: dict[str, Any] | None = None,
    capabilities: dict[str, ProviderCapabilities],
    mode: SearchMode | str = SearchMode.ADAPTIVE,
    sources: list[str] | tuple[str, ...] | None = None,
    ranking_version: str = "legacy",
    ordering: str = "relevance",
) -> SearchPlan:
    """Build a bounded adaptive, selected or all-source plan."""

    selected_mode = _coerce_mode(mode)
    active_filters = dict(filters or {})
    requested = tuple(dict.fromkeys(str(item) for item in (sources or ())))
    if selected_mode is SearchMode.SELECTED:
        source_names = requested
    else:
        eligible = [
            capability
            for capability in capabilities.values()
            if _eligible(capability, allow_context=selected_mode is SearchMode.ALL)
        ]
        ranked = sorted(eligible, key=lambda item: _eligibility_key(item, active_filters))
        selected = (
            ranked
            if selected_mode is SearchMode.ALL
            else _select_diverse(ranked, limit=MAX_ADAPTIVE_SOURCES)
        )
        source_names = tuple(capability.source for capability in selected)
    source_names = tuple(dict.fromkeys(source_names))
    omitted = tuple(
        sorted(
            source
            for source in capabilities
            if source not in source_names and selected_mode is not SearchMode.SELECTED
        )
    )
    intent = SearchIntent(
        text=text,
        filters=active_filters,
        sources=source_names,
        ordering=ordering,
    )
    provider_plans = {plan.source: plan for plan in plan_federated_query(intent, capabilities)}
    waves = _waves(source_names)
    plan_id = _plan_id(
        intent=intent,
        mode=selected_mode,
        ranking_version=ranking_version,
        waves=waves,
    )
    return SearchPlan(
        plan_id=plan_id,
        planner_version=PLANNER_VERSION,
        mode=selected_mode,
        intent=intent,
        sources=source_names,
        waves=waves,
        provider_plans=provider_plans,
        ranking_version=ranking_version,
        omitted_sources=omitted,
    )


def _coerce_mode(value: SearchMode | str) -> SearchMode:
    try:
        return value if isinstance(value, SearchMode) else SearchMode(str(value))
    except ValueError as exc:
        raise ValueError("mode must be adaptive, selected or all") from exc


def _eligible(capability: ProviderCapabilities, *, allow_context: bool) -> bool:
    if not capability.supports_unified_search:
        return False
    # A declared access contract without a public state is not a safe default
    # candidate. The source remains visible to explicit diagnostics.
    if capability.access_statuses and not any(
        str(status) in {"public", "AccessStatus.PUBLIC"} for status in capability.access_statuses
    ):
        return False
    if capability.category not in JURISPRUDENCE_CATEGORIES:
        return allow_context and capability.category == "specialized_context"
    return True


def _eligibility_key(
    capability: ProviderCapabilities,
    filters: dict[str, Any],
) -> tuple[Any, ...]:
    supported = sum(
        1
        for name, value in filters.items()
        if value and capability.filter_status(name) in {"native", "translated", "validated_scope"}
    )
    full_text = int(
        capability.supports_full_text
        or capability.full_text_access in {"detail_call", "document_link"}
    )
    pagination = int(capability.pagination_mode not in {"unknown", ""})
    category_rank = {
        "court_jurisprudence": 0,
        "jurisprudence": 0,
        "curated_jurisprudence": 1,
        "administrative_jurisprudence": 2,
        "court_precedents": 3,
        "qualified_precedents": 3,
        "electoral_jurisprudence": 2,
    }.get(capability.category, 9)
    return (
        -supported,
        -full_text,
        -pagination,
        category_rank,
        _authority(capability.source),
        capability.source,
    )


def _authority(source: str) -> str:
    match = re.match(
        r"(stf|stj|tst|tse|stm|cnj|cjf|trf\d|trt\d{1,2}|tj[a-z]{2}|tce[_-]?[a-z]{2})",
        source.casefold(),
    )
    return match.group(1) if match else source.casefold().split("_", 1)[0]


def _select_diverse(
    ranked: list[ProviderCapabilities], *, limit: int
) -> list[ProviderCapabilities]:
    """Prefer one source per authority before filling the quality ranking."""

    chosen: list[ProviderCapabilities] = []
    seen_authorities: set[str] = set()
    for capability in ranked:
        authority = _authority(capability.source)
        if authority in seen_authorities:
            continue
        chosen.append(capability)
        seen_authorities.add(authority)
        if len(chosen) == limit:
            return chosen
    for capability in ranked:
        if capability not in chosen:
            chosen.append(capability)
            if len(chosen) == limit:
                break
    return chosen


def _waves(sources: tuple[str, ...]) -> tuple[SourceWave, ...]:
    if not sources:
        return ()
    chunks = (sources[:3], sources[3:7], sources[7:])
    return tuple(
        SourceWave(number=index, sources=tuple(chunk))
        for index, chunk in enumerate(chunks, start=1)
        if chunk
    )


def _plan_id(
    *,
    intent: SearchIntent,
    mode: SearchMode,
    ranking_version: str,
    waves: tuple[SourceWave, ...],
) -> str:
    payload = {
        "planner": PLANNER_VERSION,
        "mode": mode.value,
        "intent": intent.fingerprint(),
        "ranking_version": ranking_version,
        "waves": [wave.to_dict() for wave in waves],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:24]


__all__ = [
    "DEFAULT_SOURCE_TIMEOUT_SECONDS",
    "DEFAULT_WAVE_TIMEOUT_SECONDS",
    "GLOBAL_CANDIDATE_BUDGET",
    "MAX_ADAPTIVE_SOURCES",
    "MIN_ADAPTIVE_SOURCES",
    "PER_SOURCE_CANDIDATE_BUDGET",
    "PLANNER_VERSION",
    "SearchMode",
    "SearchPlan",
    "SourceWave",
    "plan_live_search",
]
