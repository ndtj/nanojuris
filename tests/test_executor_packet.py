from __future__ import annotations

from tools.validate_executor_packet import validate_packet


def test_executor_packet_matches_open_task_audit() -> None:
    result = validate_packet()
    assert result["status"] == "pass"
    assert result["open_tasks"] == 63
    assert result["by_classification"] == {
        "external_source": 45,
        "human_review": 18,
    }
