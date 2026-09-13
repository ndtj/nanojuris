from __future__ import annotations

import json
from pathlib import Path

ARTIFACT = (
    Path(__file__).parents[1]
    / "docs"
    / "provider-discovery"
    / "stf-informativo-live-recheck-20260901-cycle1.json"
)


def test_stf_informativo_recheck_preserves_blocked_states() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    assert payload["source_id"] == "stf_informativo"
    assert payload["credentials_used"] is False
    assert payload["raw_content_persisted"] is False
    attempts = payload["attempts"]
    assert [attempt["classification"] for attempt in attempts] == [
        "blocked_transport",
        "blocked_access",
    ]
    assert attempts[1]["http_status"] == 403
    assert attempts[1]["response_bytes"] == 118
    assert "total" not in payload
    assert payload["promotion_decision"] == "runtime_unchanged"
