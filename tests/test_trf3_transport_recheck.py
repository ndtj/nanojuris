from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_trf3_recheck_keeps_transport_failures_distinct_from_empty_data() -> None:
    path = ROOT / "docs/provider-discovery/trf3-live-recheck-20260901-cycle3.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["source_id"] == "trf3_jurisprudencia"
    assert payload["credentials_used"] is False
    assert payload["raw_content_persisted"] is False
    assert len(payload["routes"]) == 3
    assert {row["classification"] for row in payload["routes"]} == {"blocked_transport"}
    assert all(row["http_status"] is None for row in payload["routes"])
    assert payload["promotion_decision"] == "candidate_only"
