"""Deterministic continuous certification for provider evidence.

Certification is intentionally read-only: it evaluates bounded evidence and
returns a manifest. It never changes provider registration, performs a live
request, or turns an unavailable source into an empty result.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


class FreshnessStatus(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    MISSING = "missing"
    INVALID = "invalid"


class CertificationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


@dataclass(frozen=True, slots=True)
class CertificationPolicy:
    """Bounded certification thresholds; all values are explicit."""

    default_ttl_seconds: int = 86_400
    minimum_completeness: float = 0.80
    daily_risk_levels: tuple[str, ...] = ("critical", "high")
    weekly_risk_levels: tuple[str, ...] = ("medium",)

    def __post_init__(self) -> None:
        if self.default_ttl_seconds <= 0:
            raise ValueError("default_ttl_seconds must be positive")
        if not 0 <= self.minimum_completeness <= 1:
            raise ValueError("minimum_completeness must be between zero and one")

    def ttl_for(self, risk_level: str) -> int:
        risk = risk_level.strip().lower()
        if risk in self.daily_risk_levels:
            return self.default_ttl_seconds
        if risk in self.weekly_risk_levels:
            return self.default_ttl_seconds * 7
        return self.default_ttl_seconds * 30

    def to_dict(self) -> dict[str, Any]:
        return {
            "default_ttl_seconds": self.default_ttl_seconds,
            "minimum_completeness": self.minimum_completeness,
            "daily_risk_levels": list(self.daily_risk_levels),
            "weekly_risk_levels": list(self.weekly_risk_levels),
        }


@dataclass(frozen=True, slots=True)
class ProviderEvidenceSnapshot:
    """Sanitized evidence used by the certification evaluator."""

    provider: str
    observed_at: str | None
    outcome: str
    schema_fingerprint: str | None = None
    route_fingerprint: str | None = None
    selector_fingerprint: str | None = None
    completeness: float | None = None
    parser_version: str | None = None
    evidence_id: str | None = None
    risk_level: str = "medium"

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        if not self.outcome.strip():
            raise ValueError("outcome must not be empty")
        if self.completeness is not None and not 0 <= self.completeness <= 1:
            raise ValueError("completeness must be between zero and one")

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "observed_at": self.observed_at,
            "outcome": self.outcome,
            "schema_fingerprint": self.schema_fingerprint,
            "route_fingerprint": self.route_fingerprint,
            "selector_fingerprint": self.selector_fingerprint,
            "completeness": self.completeness,
            "parser_version": self.parser_version,
            "evidence_id": self.evidence_id,
            "risk_level": self.risk_level,
        }


@dataclass(frozen=True, slots=True)
class CertificationAlert:
    code: str
    severity: CertificationSeverity
    message: str
    blocks_promotion: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "blocks_promotion": self.blocks_promotion,
        }


@dataclass(frozen=True, slots=True)
class CertificationReport:
    provider: str
    freshness: FreshnessStatus
    alerts: tuple[CertificationAlert, ...]
    can_promote: bool
    recommended_smoke: str
    parser_version: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "freshness": self.freshness.value,
            "alerts": [alert.to_dict() for alert in self.alerts],
            "can_promote": self.can_promote,
            "recommended_smoke": self.recommended_smoke,
            "parser_version": self.parser_version,
        }


@dataclass(frozen=True, slots=True)
class ParserRollbackDecision:
    """Read-only parser version selection for a reversible rollback."""

    selected_version: str
    rolled_back: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_version": self.selected_version,
            "rolled_back": self.rolled_back,
            "reason": self.reason,
        }


def classify_freshness(
    observed_at: str | None,
    *,
    now: datetime | None = None,
    ttl_seconds: int = 86_400,
) -> FreshnessStatus:
    """Classify evidence age without silently accepting malformed timestamps."""

    if not observed_at:
        return FreshnessStatus.MISSING
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")
    try:
        observed = _parse_timestamp(observed_at)
    except ValueError:
        return FreshnessStatus.INVALID
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    age = current.astimezone(timezone.utc) - observed
    if age < timedelta(0):
        return FreshnessStatus.INVALID
    return FreshnessStatus.FRESH if age <= timedelta(seconds=ttl_seconds) else FreshnessStatus.STALE


def smoke_frequency(risk_level: str) -> str:
    """Return the bounded smoke cadence for a provider risk level."""

    risk = risk_level.strip().lower()
    if risk in {"critical", "high"}:
        return "daily"
    if risk == "medium":
        return "weekly"
    return "monthly"


def plan_parser_rollback(
    current_version: str,
    known_good_version: str | None,
    *,
    trigger: bool,
) -> ParserRollbackDecision:
    """Select a parser version without mutating a runtime or deployment.

    A rollback is allowed only to an explicitly recorded known-good version.
    Missing provenance leaves the current version selected and explains why.
    """

    current = current_version.strip()
    known_good = (known_good_version or "").strip()
    if not current:
        raise ValueError("current_version must not be empty")
    if not trigger:
        return ParserRollbackDecision(current, False, "rollback_not_requested")
    if not known_good:
        return ParserRollbackDecision(current, False, "known_good_version_missing")
    if known_good == current:
        return ParserRollbackDecision(current, False, "known_good_version_is_current")
    return ParserRollbackDecision(known_good, True, "explicit_rollback_trigger")


def certify_provider(
    current: ProviderEvidenceSnapshot,
    *,
    previous: ProviderEvidenceSnapshot | None = None,
    policy: CertificationPolicy | None = None,
    now: datetime | None = None,
) -> CertificationReport:
    """Evaluate freshness, drift, completeness and access state."""

    effective_policy = policy or CertificationPolicy()
    freshness = classify_freshness(
        current.observed_at,
        now=now,
        ttl_seconds=effective_policy.ttl_for(current.risk_level),
    )
    alerts: list[CertificationAlert] = []
    if freshness is FreshnessStatus.MISSING:
        alerts.append(_blocking("evidence_missing", "no bounded evidence timestamp"))
    elif freshness is FreshnessStatus.STALE:
        alerts.append(_blocking("evidence_expired", "bounded evidence exceeded its TTL"))
    elif freshness is FreshnessStatus.INVALID:
        alerts.append(_blocking("evidence_timestamp_invalid", "evidence timestamp is invalid"))

    if previous is not None:
        for field_name, label in (
            ("schema_fingerprint", "schema"),
            ("route_fingerprint", "route"),
            ("selector_fingerprint", "selector"),
        ):
            before = getattr(previous, field_name)
            after = getattr(current, field_name)
            if before and after and before != after:
                alerts.append(_blocking(f"{label}_drift", f"{label} fingerprint changed"))

    if current.completeness is None:
        alerts.append(_blocking("completeness_unknown", "completeness was not measured"))
    elif current.completeness < effective_policy.minimum_completeness:
        alerts.append(
            _blocking(
                "completeness_below_threshold",
                f"completeness {current.completeness:.3f} is below the configured threshold",
            )
        )

    if current.outcome in {
        "access_blocked",
        "blocked_access",
        "blocked_transport",
        "rate_limited",
        "timeout",
        "tls_error",
        "schema_invalid",
        "source_unavailable",
    }:
        alerts.append(_blocking("access_or_contract_failure", f"outcome={current.outcome}"))

    return CertificationReport(
        provider=current.provider,
        freshness=freshness,
        alerts=tuple(alerts),
        can_promote=not any(alert.blocks_promotion for alert in alerts),
        recommended_smoke=smoke_frequency(current.risk_level),
        parser_version=current.parser_version,
    )


def build_certification_manifest(
    snapshots: Iterable[ProviderEvidenceSnapshot],
    *,
    previous: Mapping[str, ProviderEvidenceSnapshot] | None = None,
    technical_gates: Mapping[str, bool] | None = None,
    policy: CertificationPolicy | None = None,
    now: datetime | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic, non-mutating certification manifest."""

    evaluated = [
        (
            snapshot,
            certify_provider(
                snapshot,
                previous=(previous or {}).get(snapshot.provider),
                policy=policy,
                now=now,
            ),
        )
        for snapshot in snapshots
    ]
    evaluated.sort(key=lambda pair: pair[0].provider)
    technical = technical_gates or {}
    report_rows: list[dict[str, Any]] = []
    for snapshot, report in evaluated:
        row = report.to_dict()
        row["technical_gate"] = technical.get(snapshot.provider, True)
        row["technical_promotion_eligible"] = bool(row["can_promote"] and row["technical_gate"])
        report_rows.append(row)
    return {
        "schema_version": "provider-certification-v1",
        "generated_at": generated_at
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "policy": (policy or CertificationPolicy()).to_dict(),
        "summary": {
            "providers": len(report_rows),
            "promotable": sum(row["technical_promotion_eligible"] for row in report_rows),
            "blocked": sum(not row["technical_promotion_eligible"] for row in report_rows),
            "by_smoke_frequency": {
                frequency: sum(row["recommended_smoke"] == frequency for row in report_rows)
                for frequency in ("daily", "weekly", "monthly")
            },
        },
        "reports": report_rows,
    }


def _blocking(code: str, message: str) -> CertificationAlert:
    return CertificationAlert(code, CertificationSeverity.BLOCKING, message, True)


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


__all__ = [
    "CertificationAlert",
    "CertificationPolicy",
    "CertificationReport",
    "CertificationSeverity",
    "FreshnessStatus",
    "ProviderEvidenceSnapshot",
    "ParserRollbackDecision",
    "build_certification_manifest",
    "certify_provider",
    "classify_freshness",
    "smoke_frequency",
    "plan_parser_rollback",
]
