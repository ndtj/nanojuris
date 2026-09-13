from __future__ import annotations

from tools.audit_0091_artifacts import build


def test_artifact_audit_reports_without_catalog_divergence() -> None:
    report = build()
    assert report["network_access"] == "not_used"
    assert report["catalog_runtime"]["divergence"] == []
    assert report["surface_workpacks"]["surface_count"] == 151
    assert report["open_tasks_are_explicit"] is True
