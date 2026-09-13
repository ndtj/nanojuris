from __future__ import annotations

import json
from pathlib import Path

ARTIFACT = (
    Path(__file__).parents[1]
    / "docs"
    / "provider-discovery"
    / "cjf-trf1-live-recheck-20260901-cycle8.json"
)


def test_cjf_trf1_recheck_preserves_access_block_and_no_body() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    assert payload["source_id"] == "cjf_jurisprudencia"
    assert payload["surface"] == "TRF1"
    assert payload["credentials_used"] is False
    assert payload["raw_content_persisted"] is False
    attempts = payload["attempts"]
    assert len(attempts) == 1
    attempt = attempts[0]
    assert attempt["http_status"] == 200
    assert attempt["classification"] == "blocked_access"
    assert set(attempt["markers"]) == {"captcha", "recaptcha"}
    assert "total" not in payload
    assert payload["promotion_decision"] == "runtime_unchanged"
