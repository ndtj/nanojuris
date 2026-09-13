from __future__ import annotations

import json
from pathlib import Path

from tools.build_fixture_completeness import build

ROOT = Path(__file__).resolve().parents[1]


def _load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_all_runtime_providers_have_source_and_shared_scenarios() -> None:
    result = build(
        _load("docs/registry/provider-catalog.full.json"),
        _load("docs/provider-discovery/offline-audit.json"),
        _load("tests/fixtures/provider_runtime_scenarios.json"),
    )
    runtime_count = sum(
        row.get("implementation_status") == "runtime"
        for row in _load("docs/registry/provider-catalog.full.json")["entries"]
    )
    assert result["summary"]["runtime_providers"] == runtime_count
    assert result["summary"]["source_fixture_evidence"] == runtime_count
    assert result["summary"]["incomplete"] == 0
    assert not result["summary"]["incomplete_sources"]


def test_shared_scenarios_keep_external_failure_distinct_from_empty() -> None:
    scenarios = _load("tests/fixtures/provider_runtime_scenarios.json")["scenarios"]
    assert scenarios["authoritative_empty"]["result_kind"] == "real_empty"
    assert scenarios["external_failure"]["result_kind"] != "real_empty"
    assert scenarios["external_failure"]["total_state"] == "unknown"
    assert scenarios["schema_invalid"]["extraction_status"] == "schema_invalid"
    assert scenarios["second_page"]["page"] == 2
