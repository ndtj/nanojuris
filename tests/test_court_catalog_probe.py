from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
ARTIFACT = ROOT / "docs" / "topology" / "court-catalog-url-probe-20260901.json"


def test_court_catalog_probe_is_metadata_only_and_bounded() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert payload["source"] == "nanojuris.brazil.COURTS"
    assert payload["network_access"] == "public_bounded_one_request_per_url"
    assert payload["targets"] == 30
    assert payload["raw_content_persisted"] is False
    assert len(payload["results"]) == 30
    assert {item["classification"] for item in payload["results"]} == {
        "reachable",
        "access_controlled",
    }
    assert sum(item["classification"] == "reachable" for item in payload["results"]) == 2
    assert sum(item["classification"] == "access_controlled" for item in payload["results"]) == 28
    assert {item["code"] for item in payload["results"] if item["code"].startswith("TRE")} == {
        "TREAC",
        "TREAL",
        "TREAM",
        "TREAP",
        "TREBA",
        "TRECE",
        "TREDF",
        "TREES",
        "TREGO",
        "TREMA",
        "TREMG",
        "TREMS",
        "TREMT",
        "TREPA",
        "TREPB",
        "TREPE",
        "TREPI",
        "TREPR",
        "TRERJ",
        "TRERN",
        "TRERO",
        "TRERR",
        "TRERS",
        "TRESC",
        "TRESE",
        "TRESP",
        "TRETO",
    }
    assert {item["code"] for item in payload["results"] if item["code"].startswith("TJM")} == {
        "TJMMG",
        "TJMSP",
        "TJMRS",
    }
