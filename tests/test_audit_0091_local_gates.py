from __future__ import annotations

from tools.audit_0091_local_gates import build


def test_0091_local_gate_audit_is_complete_for_current_worktree() -> None:
    report = build()
    assert report["summary"]["pending"] == 0
    assert report["summary"]["catalog_entries"] >= report["summary"]["runtime_entries"]
    assert report["summary"]["open_task_classification"]["external_source"] > 0
    assert report["summary"]["open_task_classification"]["human_review"] > 0
