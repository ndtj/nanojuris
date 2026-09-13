from __future__ import annotations

import json
from pathlib import Path

from tools.audit_juscraper_reuse import audit, to_markdown

ROOT = Path(__file__).resolve().parents[1]


def test_reuse_preflight_has_clean_runtime_boundary_and_human_gate() -> None:
    report = audit(
        upstream_root=ROOT.parent.parent / ".artifacts" / "juscraper-upstream-20260901",
        intake_path=ROOT / "docs/provider-discovery/juscraper-intake-20260901.json",
        board_path=ROOT / "docs/provider-discovery/adapter-wave-board-20260901.json",
        generated_at="2026-09-01T00:00:00+00:00",
    )

    assert report["overall"] == "preflight_pass_human_review_pending"
    assert report["no_runtime_promotion"] is True
    statuses = {check["name"]: check["status"] for check in report["checks"]}
    assert statuses["upstream_license_snapshot"] == "pass"
    assert statuses["runtime_import_boundary"] == "pass"
    assert statuses["runtime_path_boundary"] == "pass"
    assert statuses["candidate_promotion_guard"] == "pass"
    assert statuses["data_redistribution_review"] == "pending_human_review"


def test_reuse_report_is_deterministic_and_explicit_about_limits() -> None:
    kwargs = {
        "upstream_root": ROOT.parent.parent / ".artifacts" / "juscraper-upstream-20260901",
        "intake_path": ROOT / "docs/provider-discovery/juscraper-intake-20260901.json",
        "board_path": ROOT / "docs/provider-discovery/adapter-wave-board-20260901.json",
        "generated_at": "2026-09-01T00:00:00+00:00",
    }
    first = audit(**kwargs)
    second = audit(**kwargs)

    assert first == second
    markdown = to_markdown(first)
    assert "nao e parecer juridico" in markdown
    assert "data_redistribution_review" in markdown
    json.dumps(first, ensure_ascii=False)
