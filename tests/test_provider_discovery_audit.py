from pathlib import Path

import pytest

from tools.audit_provider_discovery_offline import audit

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def report() -> dict:
    """Run the offline audit once and share the read-only result.

    The audit walks every fixture and test module; at ~4s per call it dominated
    the suite when each test re-ran it. Tests below only read the report.
    """

    return audit(ROOT, ROOT / "docs/registry/provider-catalog.full.json")


def test_offline_audit_finds_mapped_candidates_without_network(report: dict) -> None:
    assert report["mode"] == "offline_only"
    assert report["network_access"] == "not_used"
    assert report["summary"]["catalog_entries"] == 85
    assert report["summary"]["mapped_unimplemented"] == 0
    assert report["summary"]["diagnostic_adapters"] == 5
    # TJAP, TJSE, TRT2, Falcao, TJMSP and TJMG have checked-in diagnostic
    # adapters and fixtures; none is promoted merely because the module exists.
    assert report["summary"]["mapped_without_local_fixture"] == 0


def test_offline_audit_exercises_eproc_local_fixtures(report: dict) -> None:
    family = next(
        item
        for item in report["all_entries"]
        if item["source_id"] == "eproc_jurisprudencia_federal"
    )
    assert family["runtime_registered"] is True
    assert family["offline_evidence_status"] == "analyzed_local_fixtures"
    assert len(family["offline_discovery"]) == 3
    assert all(item["routes"] > 0 for item in family["offline_discovery"])


def test_offline_audit_separates_versioned_and_inline_runtime_evidence(report: dict) -> None:
    assert report["summary"]["runtime_providers"] == 80
    assert report["summary"]["runtime_with_versioned_fixture"] == 80
    assert report["summary"]["runtime_inline_test_only"] == 0
    assert report["summary"]["runtime_without_fixture_evidence"] == 0

    by_source = {item["source_id"]: item for item in report["all_entries"]}
    assert by_source["tjsp_nugepnac"]["fixture_evidence_kind"] == "versioned_fixture"
    assert by_source["stf_informativo"]["fixture_evidence_kind"] == "versioned_and_inline"
    assert by_source["tjpa_jurisprudencia_bff"]["fixture_evidence_kind"] == "versioned_fixture"
    assert by_source["tjsc_eproc_jurisprudencia"]["fixture_evidence_kind"] == "versioned_fixture"
    assert by_source["tjrj_eproc_jurisprudencia"]["fixture_evidence_kind"] == "versioned_fixture"
    assert by_source["tjsp_cjsg"]["fixture_evidence_kind"] == "versioned_and_inline"
    assert by_source["stf_informativo"]["inline_fixture_evidence"][0]["in_memory_builder"]


def test_offline_audit_does_not_count_fixture_files_as_test_modules(report: dict) -> None:
    for item in report["all_entries"]:
        assert all(path.endswith(".py") for path in item["test_references"])
        assert all("tests/fixtures/" not in path for path in item["test_references"])


def test_tjse_boletim_live_evidence_proves_second_degree_text() -> None:
    """Keep the bounded live evidence tied to the provider's identity contract."""

    import json

    evidence = json.loads(
        (ROOT / "docs/provider-discovery/tjse-boletim-jurisprudencia-live-20260907.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "valid"
    assert evidence["classification"] == "public_textual_second_degree"
    assert evidence["page"]["access_status"] == "public"
    assert evidence["page"]["extraction_status"] == "complete"
    assert evidence["page"]["total_known"] is False
    assert evidence["records"]
    assert evidence["detail"]["status"] == "valid"
    assert evidence["detail"]["http_status"] == 200
    assert evidence["detail"]["url"].startswith("https://")
    assert evidence["detail"]["text_length"] > 0
    assert all(
        record["authority"] == "TJSE"
        and record["degree"] == "second"
        and record["instance"] == "second"
        and record["collection"] == "CJSG"
        and record["document_type"] == "acordao"
        for record in evidence["records"]
    )
