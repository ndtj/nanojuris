from __future__ import annotations

import json
from pathlib import Path

ARTIFACT = (
    Path(__file__).parents[1]
    / "docs"
    / "provider-discovery"
    / "stf-juris-live-recheck-20260901-cycle9.json"
)


def test_stf_juris_recheck_preserves_tls_transport_failure() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    assert payload["source_id"] == "stf_juris"
    assert payload["credentials_used"] is False
    assert payload["raw_content_persisted"] is False
    result = payload["results"][0]
    assert result["classification"] == "blocked_transport"
    assert result["error_type"] == "SourceUnavailableError"
    assert result["http_status"] is None
    assert result["response_bytes"] == 0
    assert result["record_count_observed"] == 0
    assert payload["promotion_decision"] == "runtime_unchanged"
