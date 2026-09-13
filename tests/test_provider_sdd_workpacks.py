from __future__ import annotations

import json
from pathlib import Path

from tools.build_provider_sdd_workpacks import _priority, build, evidence_fingerprint

ROOT = Path(__file__).resolve().parents[1]


def test_builds_all_provider_workpacks_and_preserves_state(tmp_path: Path) -> None:
    baseline = build(ROOT, tmp_path)
    catalog = json.loads(
        (ROOT / "docs" / "registry" / "provider-catalog.full.json").read_text(encoding="utf-8")
    )
    entries = catalog["entries"]
    expected_runtime = sum(row.get("implementation_status") == "runtime" for row in entries)
    expected_candidates = sum(row.get("implementation_status") == "none" for row in entries)

    assert baseline["summary"]["providers"] == len(entries)
    assert baseline["summary"]["runtime"] == expected_runtime
    assert baseline["summary"]["candidates"] == expected_candidates
    assert baseline["topology"]["providers_reconciled"] == len(entries)
    assert baseline["topology"]["providers_unreconciled"] == 0
    assert len(list((tmp_path / "provider-workpacks").glob("*.md"))) == len(entries)

    state_path = tmp_path / "execution-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["providers"]["bnp_pangea"]["status"] = "accepted"
    state["providers"]["bnp_pangea"]["evidence"] = ["verification-example"]
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    build(ROOT, tmp_path)
    regenerated = json.loads(state_path.read_text(encoding="utf-8"))

    assert regenerated["providers"]["bnp_pangea"]["status"] == "accepted"
    assert regenerated["providers"]["bnp_pangea"]["evidence"] == ["verification-example"]

    regenerated["providers"]["bnp_pangea"]["evidence_fingerprint"] = "obsolete"
    state_path.write_text(
        json.dumps(regenerated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    build(ROOT, tmp_path)
    stale = json.loads(state_path.read_text(encoding="utf-8"))

    assert stale["providers"]["bnp_pangea"]["status"] == "stale"
    assert stale["providers"]["bnp_pangea"]["phase"] == "inspect"
    assert stale["providers"]["bnp_pangea"]["blocking_conditions"][-1]["kind"] == (
        "evidence_changed"
    )


def test_evidence_fingerprint_changes_when_evidence_changes() -> None:
    row = {
        "source_id": "example",
        "implementation_status": "runtime",
        "coverage_role": "primary_textual_jurisprudence",
        "maturity_tier": "silver",
        "maturity_score": 80,
        "target_tier": "gold",
        "priority": 1,
        "gaps": ["missing_versioned_fixture"],
    }
    original = evidence_fingerprint(row)
    row["gaps"] = []

    assert evidence_fingerprint(row) != original


def test_blocked_access_primary_provider_stays_in_p0_queue() -> None:
    entry = {
        "implementation_status": "runtime",
        "coverage_role": "primary_textual_jurisprudence",
        "maturity_tier": "silver",
        "live_status": "blocked_access",
    }

    assert _priority(entry, ["live_status:blocked_access"]) == 0


def test_migrates_legacy_terminal_states(tmp_path: Path) -> None:
    build(ROOT, tmp_path)
    state_path = tmp_path / "execution-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["providers"]["bnp_pangea"]["status"] = "complete"
    state["providers"]["bnp_pangea"]["evidence"] = ["legacy-verification"]
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    build(ROOT, tmp_path)
    migrated = json.loads(state_path.read_text(encoding="utf-8"))
    provider = migrated["providers"]["bnp_pangea"]

    assert provider["status"] == "stale"
    assert provider["evidence"] == ["legacy-verification"]
    assert provider["blocking_conditions"][-1]["kind"] == "legacy_state_migrated"
