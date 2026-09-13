from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
ARTIFACT = ROOT / "docs" / "provider-discovery" / "juscraper-semantic-diff-20260901.json"


def _record() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_semantic_diff_covers_all_inventory_surfaces() -> None:
    record = _record()
    assert record["audit_mode"] == "static_semantic_diff_no_network"
    assert record["source_repository"] == "https://github.com/jtrecenti/juscraper"
    assert record["summary"]["source_packages"] == 29
    assert record["summary"]["surface_records"] == 87
    assert record["summary"]["no_runtime_promotion"] is True
    assert len({item["source_id"] for item in record["records"]}) == 29


def test_semantic_diff_keeps_process_and_first_instance_boundaries() -> None:
    rows = _record()["records"]
    for row in rows:
        if row["surface"] in {"cpopg", "cposg"}:
            assert row["status"] == "out_of_scope"
            assert row["nanojuris"]["declared"] is False

    tjes = [row for row in rows if row["source_id"] == "tjes"]
    assert {row["surface"] for row in tjes} == {"cjsg", "cjpg", "cpopg", "cposg"}
    assert all(row["status"] == "covered_requires_differential_fixture" for row in tjes[:2])

    tjto_detail = next(
        row for row in rows if row["source_id"] == "tjto" and row["surface"] == "detail"
    )
    assert tjto_detail["status"] == "detail_contract_unverified"


def test_semantic_diff_exposes_all_contract_dimensions_without_claiming_equivalence() -> None:
    rows = _record()["records"]
    row = next(row for row in rows if row["source_id"] == "tjba" and row["surface"] == "cjsg")
    assert row["status"] == "covered_requires_differential_fixture"
    assert set(row["dimensions"]) == {"fields", "filters", "pagination", "errors", "identity"}
    assert row["dimensions"]["filters"]["status"] == "requires_name_and_behavior_mapping"
    assert row["dimensions"]["identity"]["status"] == "requires_native_id_fixture"
    assert row["promotion"].startswith("defer_until_")
