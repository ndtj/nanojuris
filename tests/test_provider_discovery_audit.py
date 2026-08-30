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
    assert report["summary"]["catalog_entries"] == 56
    assert report["summary"]["mapped_unimplemented"] == 9
    assert report["summary"]["mapped_without_local_fixture"] == 9


def test_offline_audit_exercises_eproc_local_fixtures(report: dict) -> None:
    family = next(
        item
        for item in report["family_entries"]
        if item["source_id"] == "eproc_jurisprudencia_federal"
    )
    assert family["runtime_registered"] is True
    assert family["offline_evidence_status"] == "analyzed_local_fixtures"
    assert len(family["offline_discovery"]) == 3
    assert all(item["routes"] > 0 for item in family["offline_discovery"])


def test_offline_audit_separates_versioned_and_inline_runtime_evidence(report: dict) -> None:
    assert report["summary"]["runtime_providers"] == 46
    assert report["summary"]["runtime_with_versioned_fixture"] == 43
    assert report["summary"]["runtime_inline_test_only"] == 1
    assert report["summary"]["runtime_without_fixture_evidence"] == 2

    by_source = {item["source_id"]: item for item in report["all_entries"]}
    assert by_source["tjsp_nugepnac"]["fixture_evidence_kind"] == "versioned_fixture"
    assert by_source["stf_informativo"]["fixture_evidence_kind"] == "inline_test_only"
    assert by_source["tjpa_jurisprudencia_bff"]["fixture_evidence_kind"] == "versioned_fixture"
    assert by_source["tjsc_eproc_jurisprudencia"]["fixture_evidence_kind"] == "versioned_fixture"
    # The shared eproc test intentionally reuses a TJSP response for TJRJ;
    # that must not be reported as TJRJ evidence.
    assert by_source["tjrj_eproc_jurisprudencia"]["fixture_evidence_kind"] == "none"
    assert by_source["tjsp_cjsg"]["fixture_evidence_kind"] == "versioned_and_inline"
    assert by_source["stf_informativo"]["inline_fixture_evidence"][0]["in_memory_builder"]


def test_offline_audit_does_not_count_fixture_files_as_test_modules(report: dict) -> None:
    for item in report["all_entries"]:
        assert all(path.endswith(".py") for path in item["test_references"])
        assert all("tests/fixtures/" not in path for path in item["test_references"])
