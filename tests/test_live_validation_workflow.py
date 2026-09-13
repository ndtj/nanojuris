from __future__ import annotations

from pathlib import Path


def test_live_validation_has_bounded_weekly_schedule_and_manual_defaults() -> None:
    path = Path(__file__).parents[1] / ".github" / "workflows" / "live-validation.yml"
    content = path.read_text(encoding="utf-8")
    assert 'cron: "17 4 * * 1"' in content
    assert "SOURCES: ${{ inputs.sources || 'tjdf_juris,tst_jurisprudencia' }}" in content
    assert "QUERY_TEXT: ${{ inputs.text || 'responsabilidade civil' }}" in content
    assert "TIMEOUT_SECONDS: ${{ inputs.timeout || '60' }}" in content
    assert "federated-bounded:" in content
    assert "if: github.event_name == 'schedule'" in content
    assert "run_federated_promotion_smoke.py" in content
