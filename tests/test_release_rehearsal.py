from __future__ import annotations

from pathlib import Path

from tools.build_release_rehearsal import build, render_markdown


def test_release_rehearsal_reports_missing_artifacts_without_claiming_success(
    tmp_path: Path,
) -> None:
    payload = build(tmp_path, generated_at="2026-09-02T00:00:00+00:00")

    assert payload["status"] == "failed"
    assert payload["production_action_performed"] is False
    assert payload["checks"]["wheel_present"] is False
    assert "não executadas" in render_markdown(payload)
