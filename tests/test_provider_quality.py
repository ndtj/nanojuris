from __future__ import annotations

import json
from pathlib import Path

from tools.build_provider_quality import (
    MARKDOWN_PATH,
    REPORT_PATH,
    SCENARIOS_PATH,
    build_report,
    render_markdown,
    validate_report,
)

ROOT = Path(__file__).resolve().parents[1]


def test_quality_report_is_current_and_offline() -> None:
    report = build_report()
    assert validate_report(report) == []
    assert report["scope"]["network"] is False
    assert report["summary"]["runtime"] == 80
    assert report["summary"]["critical_gap_providers"] == 0
    assert json.loads(REPORT_PATH.read_text(encoding="utf-8")) == report
    assert MARKDOWN_PATH.read_text(encoding="utf-8") == render_markdown(report)


def test_quality_scorecard_has_a_complete_dimension_contract() -> None:
    report = build_report()
    assert sum(item["weight"] for item in report["dimensions"]) == 100
    assert len(report["entries"]) == report["summary"]["providers"]
    for entry in report["entries"]:
        assert 0 <= entry["score"] <= 100
        assert entry["quality_tier"] in {"gold", "silver", "bronze", "blocked", "mapped"}
        assert set(entry["dimensions"]) == {item["id"] for item in report["dimensions"]}
        for dimension in entry["dimensions"].values():
            assert 0 <= dimension["score"] <= dimension["max"]


def test_golden_set_covers_success_and_failure_boundaries() -> None:
    payload = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    ids = {item["id"] for item in payload["scenarios"]}
    assert ids == {
        "success",
        "empty",
        "partial",
        "invalid",
        "timeout",
        "access_controlled",
        "rate_limited",
        "schema_changed",
    }
    report = build_report()
    assert report["golden_set"]["scenarios"] == sorted(
        ids,
        key=lambda item: [
            "success",
            "empty",
            "partial",
            "invalid",
            "timeout",
            "access_controlled",
            "rate_limited",
            "schema_changed",
        ].index(item),
    )


def test_quality_schema_is_checked_in() -> None:
    schema = json.loads(
        (ROOT / "docs" / "schemas" / "provider-quality.schema.json").read_text(encoding="utf-8")
    )
    assert schema["properties"]["scope"]["properties"]["network"] == {"const": False}
    assert schema["properties"]["entries"]["items"]["properties"]["quality_tier"]["enum"]
