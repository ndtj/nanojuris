from __future__ import annotations

import json
from pathlib import Path

ARTIFACT = (
    Path(__file__).parents[1]
    / "docs"
    / "provider-discovery"
    / "tjsp-cjsg-live-recheck-20260901-cycle11.json"
)


def test_tjsp_cjsg_recheck_preserves_access_control_signals() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    assert payload["source_id"] == "tjsp_cjsg"
    assert payload["credentials_used"] is False
    assert payload["raw_content_persisted"] is False
    result = payload["results"][0]
    assert result["classification"] == "blocked_access"
    assert result["error_type"] == "AccessControlRequiredError"
    assert result["record_count_observed"] == 0
    assert set(result["access_signals"]) == {
        "has_search_form",
        "has_recaptcha_field",
        "has_uuid_captcha_field",
        "has_access_control_route",
        "has_login_script",
    }
    assert payload["promotion_decision"] == "runtime_unchanged"
