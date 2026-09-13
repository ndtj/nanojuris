from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_state_eproc_detail_smoke_is_redacted() -> None:
    payload = json.loads(
        (ROOT / "docs/provider-discovery/state-eproc-detail-live-20260906.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["limits"]["bodies_persisted"] is False
    for row in payload["providers"]:
        assert "body" not in row
        assert "cookies" not in row
        assert "text" not in row.get("detail", {})
