from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
INVENTORY = ROOT / "docs" / "provider-discovery" / "juscraper-court-inventory-20260906.json"
ASSESSMENT = ROOT / "docs" / "provider-discovery" / "juscraper-parity-assessment-20260906.md"


def _inventory() -> dict:
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def test_all_upstream_state_cjsg_surfaces_have_explicit_local_classification() -> None:
    rows = [row for row in _inventory()["records"] if "cjsg" in row.get("surfaces", [])]
    assert len(rows) == 25
    assert sum(row["classification"] == "covered_by_existing_runtime" for row in rows) == 21
    assert {
        row["source_id"] for row in rows if row["classification"] == "runtime_overlap_blocked"
    } == {"tjap", "tjmg"}
    assert {
        row["source_id"]
        for row in rows
        if row["classification"] == "candidate_no_runtime_equivalent"
    } == set()


def test_parity_assessment_documents_independent_technique_boundary() -> None:
    text = ASSESSMENT.read_text(encoding="utf-8")
    for marker in ("eSAJ", "JSF/RichFaces", "SECLEVEL=1", "eproc", "GraphQL/JSON"):
        assert marker in text
    assert "não copia código" in text
    assert "TJAP e TJMG" in text
    assert "27/27" in text
