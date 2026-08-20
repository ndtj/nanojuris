from pathlib import Path

from tools.audit_provider_discovery_offline import audit

ROOT = Path(__file__).resolve().parents[1]


def test_offline_audit_finds_mapped_candidates_without_network() -> None:
    report = audit(ROOT, ROOT / "docs/registry/provider-catalog.full.json")

    assert report["mode"] == "offline_only"
    assert report["network_access"] == "not_used"
    assert report["summary"]["catalog_entries"] == 55
    assert report["summary"]["mapped_unimplemented"] == 9
    assert report["summary"]["mapped_without_local_fixture"] == 9


def test_offline_audit_exercises_eproc_local_fixtures() -> None:
    report = audit(ROOT, ROOT / "docs/registry/provider-catalog.full.json")

    family = next(
        item
        for item in report["family_entries"]
        if item["source_id"] == "eproc_jurisprudencia_federal"
    )
    assert family["runtime_registered"] is True
    assert family["offline_evidence_status"] == "analyzed_local_fixtures"
    assert len(family["offline_discovery"]) == 3
    assert all(item["routes"] > 0 for item in family["offline_discovery"])
