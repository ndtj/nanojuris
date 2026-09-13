from __future__ import annotations

from datetime import datetime, timezone

from tools.evaluate_provider_gold import evaluate


def _provider(*, live: str = "2026-09-06T00:00:00+00:00", status: str = "valid") -> dict:
    return {
        "source_id": "tj",
        "live": {"status": status, "checked_at": live},
        "contract": {"supports_unified_search": True, "filters": {"unverified": []}},
        "data": {"canonical_records": ["CanonicalDecision"], "extracted_fields": ["summary"]},
        "workpack": {
            "tasks": [
                {"id": name, "status": "complete"} for name in ("runtime_contract", "documents")
            ]
        },
        "gaps": [],
    }


def test_evaluator_separates_engineering_and_live_gold() -> None:
    report = evaluate(
        {"providers": [_provider()]},
        as_of=datetime(2026, 9, 6, tzinfo=timezone.utc),
    )
    assert report["summary"]["engineering_gold"] == 1
    assert report["summary"]["provider_gold"] == 1

    stale = evaluate(
        {"providers": [_provider(live="2026-01-01T00:00:00+00:00")]},
        as_of=datetime(2026, 9, 6, tzinfo=timezone.utc),
    )
    assert stale["summary"]["engineering_gold"] == 1
    assert stale["summary"]["provider_gold"] == 0
    assert stale["providers"][0]["freshness"] == "expired"


def test_blocked_live_status_never_becomes_provider_gold() -> None:
    report = evaluate(
        {"providers": [_provider(status="blocked")]},
        as_of=datetime(2026, 9, 6, tzinfo=timezone.utc),
    )
    assert report["summary"]["provider_gold"] == 0


def test_unverified_names_are_explicit_and_block_provider_gold() -> None:
    provider = _provider()
    provider["contract"]["filters"]["unverified"] = ["case_class", "degree"]
    provider["data"] = {
        "canonical_records": ["CanonicalDecision"],
        "field_classification": {"summary": "unknown", "source": "canonical"},
    }

    report = evaluate(
        {"providers": [provider]},
        as_of=datetime(2026, 9, 6, tzinfo=timezone.utc),
    )
    row = report["providers"][0]
    assert row["provider_gold"] is False
    assert row["unverified_filters"] == ["case_class", "degree"]
    assert row["unverified_fields"] == ["summary"]
    assert row["provider_gold_blocked_reasons"] == [
        "unverified_filters",
        "unverified_fields",
    ]
    assert report["summary"]["blocked_by_unverified_filters"] == 1
    assert report["summary"]["blocked_by_unverified_fields"] == 1
