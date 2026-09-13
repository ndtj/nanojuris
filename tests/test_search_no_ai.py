from __future__ import annotations

from tools.audit_search_no_ai import audit


def test_live_search_no_ai_gate_passes() -> None:
    result = audit()
    assert result["status"] == "pass"
    assert result["violations"] == []
