from __future__ import annotations

from tools.audit_open_tasks import _classification, build_report


def test_open_task_audit_classifies_human_and_external_work() -> None:
    report = build_report()
    assert report["open_tasks"] >= 1
    assert report["by_classification"]["external_source"] >= 1
    assert report["by_classification"]["human_review"] >= 8


def test_combined_external_human_marker_is_not_local() -> None:
    classification, _, _ = _classification("package", "T001", "E/H")
    assert classification == "human_review"
