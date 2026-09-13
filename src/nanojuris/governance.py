"""Provider rollout and release-gate decisions.

Release flags are explicit and reversible.  Technical evidence is always
required; a deployment may additionally require a human legal/reuse gate or,
when explicitly configured for local operation, an operator acceptance gate.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


class RolloutMode(str, Enum):
    OPT_IN = "opt_in"
    SHADOW = "shadow"
    ENABLED = "enabled"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class OperationalPolicy:
    """Conservative defaults for bounded public-source execution.

    This policy is deliberately explicit and serializable.  It describes the
    local technical envelope only; it never grants a source licence, allowlist
    approval or permission to deploy.
    """

    live_cache_ttl_seconds: float = 600.0
    telemetry_retention_days: int = 30
    min_provider_request_interval_seconds: float = 2.0
    max_bounded_pages: int = 3
    same_host_parallelism: int = 1
    persist_searchable_corpus: bool = False
    persist_raw_full_text: bool = False
    curated_default_rollout: RolloutMode = RolloutMode.OPT_IN
    shadow_mode_default: bool = True
    owner: str = "NanoJuris maintainer"

    def __post_init__(self) -> None:
        if self.live_cache_ttl_seconds <= 0:
            raise ValueError("live_cache_ttl_seconds must be positive")
        if self.telemetry_retention_days <= 0:
            raise ValueError("telemetry_retention_days must be positive")
        if self.min_provider_request_interval_seconds < 0:
            raise ValueError("min_provider_request_interval_seconds must be non-negative")
        if self.max_bounded_pages < 1:
            raise ValueError("max_bounded_pages must be positive")
        if self.same_host_parallelism != 1:
            raise ValueError("same_host_parallelism is fixed at one")
        if not self.owner.strip():
            raise ValueError("owner must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "live_cache_ttl_seconds": self.live_cache_ttl_seconds,
            "telemetry_retention_days": self.telemetry_retention_days,
            "min_provider_request_interval_seconds": self.min_provider_request_interval_seconds,
            "max_bounded_pages": self.max_bounded_pages,
            "same_host_parallelism": self.same_host_parallelism,
            "persist_searchable_corpus": self.persist_searchable_corpus,
            "persist_raw_full_text": self.persist_raw_full_text,
            "curated_default_rollout": self.curated_default_rollout.value,
            "shadow_mode_default": self.shadow_mode_default,
            "owner": self.owner,
        }


DEFAULT_OPERATIONAL_POLICY = OperationalPolicy()


@dataclass(frozen=True, slots=True)
class ProviderReleaseDecision:
    source: str
    mode: RolloutMode
    technical_gate: bool
    legal_gate: bool
    rollback_mode: RolloutMode
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "mode": self.mode.value,
            "technical_gate": self.technical_gate,
            "legal_gate": self.legal_gate,
            "rollback_mode": self.rollback_mode.value,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True, slots=True)
class ProviderPromotionEvidence:
    """Evidence bundle required before a source can enter federation.

    The fields deliberately keep technical and human gates separate.  A live
    HTTP response is not legal approval, and a parser fixture is not proof of
    current availability.  Keeping these dimensions explicit makes the
    promotion decision serializable and prevents a boolean shortcut from
    silently enabling a candidate provider.
    """

    source: str
    contract_valid: bool = False
    live_validated: bool = False
    fixtures_complete: bool = False
    quality_gate_passed: bool = False
    legal_approved: bool = False
    access_status: str = "unknown"
    requested_mode: RolloutMode = RolloutMode.ENABLED

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source must not be empty")
        if self.access_status not in {
            "unknown",
            "public",
            "partial",
            "blocked_access",
            "blocked_transport",
            "source_unavailable",
        }:
            raise ValueError(f"unsupported access_status: {self.access_status!r}")

    @property
    def technical_passed(self) -> bool:
        """Whether the reproducible, non-human technical gates are complete."""

        return all(
            (
                self.contract_valid,
                self.live_validated,
                self.fixtures_complete,
                self.quality_gate_passed,
            )
        ) and self.access_status not in {
            "blocked_access",
            "blocked_transport",
            "source_unavailable",
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "contract_valid": self.contract_valid,
            "live_validated": self.live_validated,
            "fixtures_complete": self.fixtures_complete,
            "quality_gate_passed": self.quality_gate_passed,
            "legal_approved": self.legal_approved,
            "access_status": self.access_status,
            "requested_mode": self.requested_mode.value,
            "technical_passed": self.technical_passed,
        }


@dataclass(frozen=True, slots=True)
class ShadowComparison:
    """Bounded, read-only comparison between baseline and candidate results."""

    baseline_count: int
    candidate_count: int
    matched_count: int
    added_ids: tuple[str, ...] = ()
    removed_ids: tuple[str, ...] = ()
    overlap_ratio: float = 0.0
    equivalent: bool = False
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_count": self.baseline_count,
            "candidate_count": self.candidate_count,
            "matched_count": self.matched_count,
            "added_ids": list(self.added_ids),
            "removed_ids": list(self.removed_ids),
            "overlap_ratio": self.overlap_ratio,
            "equivalent": self.equivalent,
            "warnings": list(self.warnings),
        }


def compare_shadow_results(
    baseline: Iterable[Any], candidate: Iterable[Any], *, max_ids: int = 10_000
) -> ShadowComparison:
    """Compare two bounded result windows without exposing result contents.

    Only stable identifiers are compared. Rows without an ``id``, ``source_id``
    or CNJ-like ``case_number`` remain visible through a warning and prevent an
    equivalence claim. The function never treats a transport failure payload as
    a result row; callers should perform status gating before invoking it.
    """

    if max_ids < 1:
        raise ValueError("max_ids must be positive")
    baseline_rows = tuple(baseline)
    candidate_rows = tuple(candidate)
    baseline_ids, baseline_unknown, baseline_duplicates = _shadow_ids(baseline_rows, max_ids)
    candidate_ids, candidate_unknown, candidate_duplicates = _shadow_ids(candidate_rows, max_ids)
    matched = baseline_ids & candidate_ids
    union = baseline_ids | candidate_ids
    warnings: list[str] = []
    if baseline_unknown or candidate_unknown:
        warnings.append("rows_without_stable_identity")
    if baseline_duplicates or candidate_duplicates:
        warnings.append("duplicate_stable_identity")
    if len(baseline_rows) > max_ids or len(candidate_rows) > max_ids:
        warnings.append("comparison_window_truncated")
    if len(baseline_rows) != len(candidate_rows):
        warnings.append("result_count_changed")
    if baseline_ids != candidate_ids:
        warnings.append("stable_identity_set_changed")
    return ShadowComparison(
        baseline_count=len(baseline_rows),
        candidate_count=len(candidate_rows),
        matched_count=len(matched),
        added_ids=tuple(sorted(candidate_ids - baseline_ids)),
        removed_ids=tuple(sorted(baseline_ids - candidate_ids)),
        overlap_ratio=(len(matched) / len(union)) if union else 1.0,
        equivalent=not warnings and baseline_ids == candidate_ids,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _shadow_ids(rows: tuple[Any, ...], max_ids: int) -> tuple[set[str], bool, bool]:
    identifiers: list[str] = []
    unknown = False
    for row in rows[:max_ids]:
        identifier = _shadow_id(row)
        if identifier is None:
            unknown = True
        else:
            identifiers.append(identifier)
    return set(identifiers), unknown, len(identifiers) != len(set(identifiers))


def _shadow_id(row: Any) -> str | None:
    values: list[Any] = []
    if isinstance(row, Mapping):
        values.extend(row.get(name) for name in ("id", "source_id", "case_number"))
    else:
        values.extend(getattr(row, name, None) for name in ("id", "source_id", "case_number"))
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return None


def evaluate_release_gate(
    *,
    source: str,
    technical_passed: bool,
    legal_approved: bool,
    requested_mode: RolloutMode = RolloutMode.ENABLED,
    has_reproducible_fixture: bool = True,
) -> ProviderReleaseDecision:
    """Return a deterministic promotion decision without changing runtime state."""

    if not source.strip():
        raise ValueError("source must not be empty")
    reasons: list[str] = []
    if not technical_passed:
        reasons.append("technical_gate_failed")
    if not has_reproducible_fixture:
        reasons.append("reproducible_fixture_missing")
    if not legal_approved:
        reasons.append("human_legal_reuse_gate_pending")
    if requested_mode is RolloutMode.BLOCKED or reasons:
        mode = RolloutMode.BLOCKED if requested_mode is RolloutMode.BLOCKED else RolloutMode.OPT_IN
    elif requested_mode is RolloutMode.ENABLED:
        mode = RolloutMode.ENABLED
    else:
        mode = requested_mode
    return ProviderReleaseDecision(
        source=source,
        mode=mode,
        technical_gate=technical_passed and has_reproducible_fixture,
        legal_gate=legal_approved,
        rollback_mode=RolloutMode.OPT_IN,
        reasons=tuple(reasons),
    )


def evaluate_provider_promotion(
    evidence: ProviderPromotionEvidence,
) -> ProviderReleaseDecision:
    """Evaluate all promotion gates without mutating runtime registration.

    This is the preferred API for release tooling.  ``evaluate_release_gate``
    remains available for legacy callers that only have a single technical
    boolean, while this function refuses to collapse live, fixture, quality,
    access and human approval evidence into one unchecked flag.
    """

    reasons: list[str] = []
    if not evidence.contract_valid:
        reasons.append("contract_gate_failed")
    if not evidence.live_validated:
        reasons.append("live_validation_missing")
    if not evidence.fixtures_complete:
        reasons.append("reproducible_fixture_missing")
    if not evidence.quality_gate_passed:
        reasons.append("quality_gate_failed")
    if evidence.access_status in {"blocked_access", "blocked_transport", "source_unavailable"}:
        reasons.append(evidence.access_status)
    if not evidence.legal_approved:
        reasons.append("human_legal_reuse_gate_pending")

    if evidence.requested_mode is RolloutMode.BLOCKED:
        mode = RolloutMode.BLOCKED
    elif evidence.access_status in {"blocked_access", "blocked_transport", "source_unavailable"}:
        mode = RolloutMode.BLOCKED
    elif reasons:
        mode = RolloutMode.OPT_IN
    else:
        mode = evidence.requested_mode

    return ProviderReleaseDecision(
        source=evidence.source,
        mode=mode,
        technical_gate=evidence.technical_passed,
        legal_gate=evidence.legal_approved,
        rollback_mode=RolloutMode.OPT_IN,
        reasons=tuple(dict.fromkeys(reasons)),
    )


__all__ = [
    "OperationalPolicy",
    "DEFAULT_OPERATIONAL_POLICY",
    "ShadowComparison",
    "ProviderPromotionEvidence",
    "ProviderReleaseDecision",
    "RolloutMode",
    "evaluate_provider_promotion",
    "evaluate_release_gate",
    "compare_shadow_results",
]
