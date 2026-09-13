from __future__ import annotations

import json
from pathlib import Path

from tools.complete_provider_workpacks import apply_completion, classify_provider

ROOT = Path(__file__).resolve().parents[1]


def test_technical_ready_source_is_accepted_with_explicit_limitations() -> None:
    result = classify_provider(
        {
            "source_id": "example",
            "implementation_status": "runtime",
            "live_status": "valid",
        },
        {
            "source": "example",
            "mode": "enabled",
            "technical_gate": True,
            "live_status": "valid",
            "access_status": "public",
        },
    )

    assert result["disposition"] == "accepted_with_limitations"
    assert result["status"] == "ready_for_review"
    assert result["operational_health"] == "valid"
    assert result["review_after"] is None


def test_blocked_source_is_deferred_without_becoming_empty() -> None:
    result = classify_provider(
        {
            "source_id": "blocked",
            "implementation_status": "runtime",
            "live_status": "blocked_transport",
        },
        {
            "source": "blocked",
            "mode": "blocked",
            "technical_gate": False,
            "reasons": ["blocked_transport"],
            "live_status": "blocked_transport",
            "access_status": "blocked_transport",
        },
    )

    assert result["disposition"] == "deferred_with_review"
    assert result["status"] == "waiting_evidence"
    assert result["operational_health"] == "tls_error"
    assert result["review_after"]
    assert "transport" in result["resume_when"]
    assert result["blocking_conditions"][0]["kind"] == "completion_decision"


def test_completion_run_populates_every_provider_and_workpack(tmp_path: Path) -> None:
    result = apply_completion(ROOT, tmp_path, write=True)
    assert result["summary"]["providers"] == 85
    assert result["summary"]["terminal"] == 85

    state = json.loads((tmp_path / "execution-state.json").read_text(encoding="utf-8"))
    providers = state["providers"]
    assert len(providers) == 85
    assert all(item["disposition"] for item in providers.values())
    assert all(item["status"] != "not_started" for item in providers.values())
    workpacks = list((tmp_path / "provider-workpacks").glob("*.md"))
    assert len(workpacks) == 85
    assert not any(
        line.lstrip().startswith("- [ ] WP-")
        for path in workpacks
        for line in path.read_text(encoding="utf-8").splitlines()
    )

    before = json.loads((tmp_path / "execution-state.json").read_text(encoding="utf-8"))
    apply_completion(ROOT, tmp_path, write=True)
    after = json.loads((tmp_path / "execution-state.json").read_text(encoding="utf-8"))
    for source in before["providers"]:
        assert (
            after["providers"][source]["disposition"] == before["providers"][source]["disposition"]
        )
        assert len(after["providers"][source]["blocking_conditions"]) == len(
            before["providers"][source]["blocking_conditions"]
        )
