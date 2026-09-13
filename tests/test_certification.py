from __future__ import annotations

from datetime import datetime, timezone

from nanojuris.certification import (
    CertificationPolicy,
    FreshnessStatus,
    ProviderEvidenceSnapshot,
    build_certification_manifest,
    certify_provider,
    classify_freshness,
    plan_parser_rollback,
    smoke_frequency,
)
from tools.build_provider_certification import build

NOW = datetime(2026, 9, 7, 12, tzinfo=timezone.utc)


def _snapshot(**overrides: object) -> ProviderEvidenceSnapshot:
    values: dict[str, object] = {
        "provider": "fixture",
        "observed_at": "2026-09-07T11:00:00+00:00",
        "outcome": "success_with_results",
        "schema_fingerprint": "schema-a",
        "route_fingerprint": "route-a",
        "selector_fingerprint": "selector-a",
        "completeness": 0.95,
        "parser_version": "parser-1",
        "risk_level": "high",
    }
    values.update(overrides)
    return ProviderEvidenceSnapshot(**values)


def test_freshness_distinguishes_missing_stale_invalid_and_fresh() -> None:
    assert classify_freshness(None, now=NOW) is FreshnessStatus.MISSING
    assert (
        classify_freshness("2026-09-01T00:00:00Z", now=NOW, ttl_seconds=3600)
        is FreshnessStatus.STALE
    )
    assert classify_freshness("not-a-date", now=NOW) is FreshnessStatus.INVALID
    assert (
        classify_freshness("2026-09-07T11:30:00Z", now=NOW, ttl_seconds=3600)
        is FreshnessStatus.FRESH
    )


def test_risk_levels_map_to_bounded_smoke_cadence() -> None:
    assert smoke_frequency("critical") == "daily"
    assert smoke_frequency("medium") == "weekly"
    assert smoke_frequency("low") == "monthly"
    policy = CertificationPolicy(default_ttl_seconds=100)
    assert policy.ttl_for("high") == 100
    assert policy.ttl_for("medium") == 700
    assert policy.ttl_for("low") == 3000


def test_schema_route_and_selector_drift_blocks_promotion() -> None:
    current = _snapshot(schema_fingerprint="schema-b", route_fingerprint="route-b")
    report = certify_provider(current, previous=_snapshot(), now=NOW)
    assert report.can_promote is False
    assert {alert.code for alert in report.alerts} >= {"schema_drift", "route_drift"}


def test_unknown_completeness_and_external_failure_block() -> None:
    report = certify_provider(_snapshot(completeness=None, outcome="access_blocked"), now=NOW)
    assert report.can_promote is False
    assert {alert.code for alert in report.alerts} >= {
        "completeness_unknown",
        "access_or_contract_failure",
    }


def test_complete_fresh_snapshot_is_eligible_technically() -> None:
    report = certify_provider(_snapshot(), now=NOW)
    assert report.can_promote is True
    assert report.freshness is FreshnessStatus.FRESH
    assert report.recommended_smoke == "daily"


def test_parser_rollback_requires_explicit_known_good_version() -> None:
    unchanged = plan_parser_rollback("parser-2", None, trigger=True)
    assert unchanged.rolled_back is False
    assert unchanged.reason == "known_good_version_missing"

    rolled_back = plan_parser_rollback("parser-2", "parser-1", trigger=True)
    assert rolled_back.rolled_back is True
    assert rolled_back.selected_version == "parser-1"

    no_trigger = plan_parser_rollback("parser-2", "parser-1", trigger=False)
    assert no_trigger.selected_version == "parser-2"


def test_manifest_is_sorted_and_counts_blocked_reports() -> None:
    manifest = build_certification_manifest(
        [_snapshot(provider="z"), _snapshot(provider="a", completeness=None)],
        now=NOW,
        generated_at="2026-09-07T12:00:00Z",
    )
    assert manifest["summary"] == {
        "providers": 2,
        "promotable": 1,
        "blocked": 1,
        "by_smoke_frequency": {"daily": 2, "weekly": 0, "monthly": 0},
    }
    assert [row["provider"] for row in manifest["reports"]] == ["a", "z"]


def test_generated_catalog_manifest_is_explicitly_conservative() -> None:
    manifest = build(generated_at="2026-09-07T12:00:00Z")
    assert manifest["schema_version"] == "provider-certification-v1"
    assert manifest["summary"]["providers"] == 85
    assert manifest["summary"]["promotable"] == 0
    assert all(report["alerts"] for report in manifest["reports"])
