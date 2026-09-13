from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
ARTIFACT = ROOT / "docs" / "provider-discovery" / "juscraper-intake-20260901.json"
SMOKE_ARTIFACT = ROOT / "docs" / "provider-discovery" / "juscraper-live-smoke-20260901.json"
RECHECK_ARTIFACT = ROOT / "docs" / "provider-discovery" / "juscraper-live-recheck-20260901.json"


def test_juscraper_intake_records_brazilian_candidates_without_promoting_them() -> None:
    record = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    upstream = record["upstream"]

    assert upstream["repository"] == "https://github.com/jtrecenti/juscraper"
    assert upstream["commit"]
    assert upstream["license_declared"] == "MIT"
    assert upstream["version"] == "0.3.0"
    assert record["audit_mode"] == "static_source_only"
    assert record["live_availability_claim"] is False
    scope = record["observed_scope"]
    assert scope["brazilian_court_packages"] == 25
    assert scope["brazilian_source_ids"] == [
        "tjac",
        "tjal",
        "tjam",
        "tjap",
        "tjba",
        "tjce",
        "tjdft",
        "tjes",
        "tjgo",
        "tjmg",
        "tjms",
        "tjmt",
        "tjpa",
        "tjpb",
        "tjpe",
        "tjpi",
        "tjpr",
        "tjrj",
        "tjrn",
        "tjro",
        "tjrr",
        "tjrs",
        "tjsc",
        "tjsp",
        "tjto",
    ]
    assert record["nanojuris_surface_decisions"]["cjsg"]["classification"] == "candidate"
    assert record["nanojuris_action"]["copied_upstream_code"] is False


def test_juriscraper_intake_has_no_runtime_action() -> None:
    record = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    action = record["nanojuris_action"]

    assert action["runtime_change"] == "none"
    assert action["required_before_adapter"]


def test_juscraper_live_smoke_is_bounded_and_keeps_candidates_unpromoted() -> None:
    record = json.loads(SMOKE_ARTIFACT.read_text(encoding="utf-8"))

    assert record["audit_mode"] == "bounded_public_http_smoke"
    assert record["frequency"] == "one request per endpoint"
    assert record["raw_content_persisted"] is False
    assert record["credentials_used"] is False
    results = {item["provider"]: item for item in record["results"]}
    assert set(results) == {"tjes", "tjrn"}
    for item in results.values():
        assert item["status"] == 200
        assert item["retrieval_status"] == "ok"
        assert item["classification"] == "candidate_live_valid_data"
        assert item["identity_field_present"] is True
        assert item["summary_field_present"] is True
    assert record["promotion_decision"] == "candidate_only"
    assert record["promotion_blockers"]


def test_juscraper_live_recheck_preserves_blocked_access_as_distinct_state() -> None:
    record = json.loads(RECHECK_ARTIFACT.read_text(encoding="utf-8"))

    assert record["audit_mode"] == "bounded_public_http_recheck"
    assert record["credentials_used"] is False
    assert record["raw_content_persisted"] is False
    results = {item["source_id"]: item for item in record["results"]}
    assert results["tjes_jurisprudencia"]["classification"] == "reachable_valid_data"
    assert results["tjes_jurisprudencia"]["record_count_observed"] == 1
    assert results["tjrn_jurisprudencia"]["http_status"] == 403
    assert results["tjrn_jurisprudencia"]["classification"] == "blocked_access"
    assert results["tjrn_jurisprudencia"]["record_count_observed"] is None
    assert record["promotion_decision"] == "candidate_only"
