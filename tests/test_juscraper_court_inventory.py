from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
ARTIFACT = ROOT / "docs" / "provider-discovery" / "juscraper-court-inventory-20260901.json"
MARKDOWN_ARTIFACT = ROOT / "docs" / "provider-discovery" / "juscraper-court-inventory-20260901.md"


def _record() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_inventory_covers_all_upstream_court_packages() -> None:
    record = _record()
    summary = record["summary"]
    assert summary["state_court_packages"] == 25
    assert summary["trf_packages"] == 4
    assert summary["total_court_packages"] == 29
    assert len(record["records"]) == 29
    assert all(item["upstream_client_class"] for item in record["records"])
    assert record["upstream"]["repository"] == "https://github.com/jtrecenti/juscraper"
    assert record["schema_version"] == 2
    assert record["audit_mode"] == "static_inventory_no_network"
    assert record["nanojuris"]["court_catalog_count"] == 94
    assert (
        record["nanojuris"]["court_catalog_exhaustiveness"]
        == "cnj_register_snapshot_with_local_metadata"
    )
    assert record["nanojuris"]["juscraper_overlap_count"] == 29
    assert len(record["nanojuris"]["courts_not_in_juscraper"]) == 65
    assert "tjse" in record["nanojuris"]["courts_not_in_juscraper"]
    assert "trt1" in record["nanojuris"]["courts_not_in_juscraper"]
    assert len(record["catalog_limitations"]) == 3
    assert record["evidence_artifacts"] == [
        "docs/topology/cnj-tribunal-register-20260901.json",
        "docs/topology/court-catalog-url-probe-20260901.json",
    ]


def test_inventory_reconciles_promoted_runtime_from_process_surfaces() -> None:
    record = {item["source_id"]: item for item in _record()["records"]}
    assert record["tjes"]["classification"] == "covered_by_existing_runtime"
    assert record["tjrn"]["classification"] == "covered_by_existing_runtime"
    assert record["tjes"]["surface_equivalents"]["cjpg"] == "tjes_cjpg"
    assert record["tjes"]["surface_equivalents"]["cjsg"] == "tjes_jurisprudencia"
    assert record["tjrn"]["nanojuris_equivalent"] == "tjrn_jurisprudencia"
    assert record["tjro"]["nanojuris_equivalent"] == "tjro_jurisprudencia"
    assert "tjro_liame" not in record["tjro"]["nanojuris_equivalents"]
    assert "detail" in record["tjto"]["surfaces"]
    for source_id in ("trf1", "trf3", "trf5", "trf6"):
        assert record[source_id]["classification"] == "out_of_scope_process_surface"
        assert record[source_id]["surfaces"] == ["cpopg", "cposg"]


def test_inventory_never_claims_blocked_surface_as_covered() -> None:
    record = {item["source_id"]: item for item in _record()["records"]}
    for source_id, provider in (("tjap", "tjap_tucujuris"), ("tjmg", "tjmg_jurisprudencia")):
        assert record[source_id]["classification"] == "runtime_overlap_blocked"
        assert record[source_id]["surface_equivalents"]["cjsg"] == provider
        assert record[source_id]["blocked_runtime_equivalents"] == [provider]


def test_inventory_does_not_claim_equivalence_from_names_only() -> None:
    record = {item["source_id"]: item for item in _record()["records"]}
    assert record["tjrj"]["classification"] == "partial_overlap_review"
    assert record["tjsc"]["classification"] == "partial_overlap_review"
    assert all(
        item["equivalent_registered"]
        for item in record.values()
        if item["nanojuris_equivalent"] and item["classification"] != "out_of_scope_process_surface"
    )


def test_markdown_inventory_lists_national_catalog_gaps() -> None:
    markdown = MARKDOWN_ARTIFACT.read_text(encoding="utf-8")
    assert "Autoridades no catálogo NanoJuris sem pacote Juscraper" in markdown
    assert markdown.count("not_in_juscraper_catalog_gap") == 65
