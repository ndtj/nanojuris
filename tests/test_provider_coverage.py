from __future__ import annotations

import json
from pathlib import Path

from nanojuris.catalog import get_provider_catalog_entry, load_provider_catalog
from nanojuris.client import NanoJurisClient
from tools import build_provider_coverage as coverage_builder
from tools.build_provider_coverage import build_catalog, render_docs

ROOT = Path(__file__).resolve().parents[1]


def test_provider_coverage_catalog_is_current() -> None:
    catalog_path = ROOT / "docs" / "registry" / "provider-catalog.full.json"
    expected = build_catalog()
    actual = json.loads(catalog_path.read_text(encoding="utf-8"))

    assert actual == expected


def test_packaged_catalog_matches_documentation_catalog() -> None:
    documentation_catalog = json.loads(
        (ROOT / "docs" / "registry" / "provider-catalog.full.json").read_text(encoding="utf-8")
    )

    assert load_provider_catalog() == documentation_catalog
    assert get_provider_catalog_entry("tjdf_juris")["source_id"] == "tjdf_juris"


def test_provider_coverage_docs_are_current() -> None:
    catalog = build_catalog()

    for path, expected in render_docs(catalog).items():
        assert path.is_file(), str(path)
        assert path.read_text(encoding="utf-8") == expected, str(path)


def test_provider_coverage_catalog_matches_runtime_sources() -> None:
    catalog = build_catalog()
    entries = {entry["source_id"]: entry for entry in catalog["entries"]}
    runtime_sources = {item.source for item in NanoJurisClient().list_sources()}
    implemented = {
        source_id for source_id, entry in entries.items() if entry["lifecycle"] == "implemented"
    }

    assert implemented == runtime_sources

    for source_id in runtime_sources:
        entry = entries[source_id]
        assert entry["documentation"]["human_doc"] == f"docs/providers/{source_id}/README.md"
        assert (
            entry["input_contract"]["search_modes"]
            == (entry["source_contract"]["evidence"]["search_modes"])
        )
        assert (
            entry["output_contract"]["canonical_records"]
            == (entry["source_contract"]["evidence"]["canonical_records"])
        )


def test_primary_textual_sources_are_suitable_for_unified_jurisprudence() -> None:
    catalog = build_catalog()
    primary = [
        entry
        for entry in catalog["entries"]
        if entry["coverage_role"] == "primary_textual_jurisprudence"
    ]

    assert primary
    for entry in primary:
        assert entry["lifecycle"] == "implemented"
        assert entry["interfaces"]["unified_search"] is True
        assert "CanonicalDecision" in entry["output_contract"]["canonical_records"]


def test_provider_coverage_scores_are_actionable() -> None:
    catalog = build_catalog()

    for entry in catalog["entries"]:
        score = entry["maturity_score"]
        assert 0 <= score["total"] <= 100, entry["source_id"]
        assert score["grade"] in {"A", "B", "C", "D"}, entry["source_id"]
        assert set(score["dimensions"]) == {
            "input",
            "output",
            "reliability",
            "documentation",
            "product",
        }
        assert score["next_actions"], entry["source_id"]


def test_reference_provider_scores_above_mapped_candidates() -> None:
    catalog = build_catalog()
    entries = {entry["source_id"]: entry for entry in catalog["entries"]}

    assert entries["tjdf_juris"]["maturity_score"]["total"] >= 85
    for entry in catalog["entries"]:
        if entry["lifecycle"] == "candidate":
            assert (
                entry["maturity_score"]["total"] < entries["tjdf_juris"]["maturity_score"]["total"]
            )


def test_standalone_document_evidence_is_consumed_by_catalog(monkeypatch, tmp_path) -> None:
    artifact = {
        "source": "stj_scon",
        "scope": "public_full_text_document",
        "checked_at": "2026-08-16T16:15:00-03:00",
        "document_id": "stj-scon-document-202502858982",
        "status": "valid",
        "http_status": 200,
        "access_status": "public",
        "retrieval_status": "ok",
        "extraction_status": "complete",
        "full_text_status": "loaded",
        "content_type": "application/pdf",
        "response_bytes": 270212,
        "sha256": "a" * 64,
        "parser": "stj_scon.get_document",
    }
    (tmp_path / "document.json").write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "VALIDATION_RUNS_DIR", tmp_path)

    rows = coverage_builder._parse_validation_runs()

    assert rows["stj_scon"]["status"] == "valid"
    assert rows["stj_scon"]["scope"] == "public_full_text_document"
    assert rows["stj_scon"]["full_text_status"] == "loaded"
    assert rows["stj_scon"]["sha256"] == "a" * 64
    assert rows["stj_scon"]["evidence"].endswith("/document.json")


def test_validation_envelope_sources_are_consumed(monkeypatch, tmp_path) -> None:
    artifact = {
        "checked_at": "2026-08-16T12:56:03Z",
        "scope": "missing_state_providers_live",
        "sources": [
            {
                "source_id": "tjro_liame",
                "checked_at": "2026-08-16T12:56:03Z",
                "status": "valid",
                "http_status": 200,
                "access_status": "public",
                "retrieval_status": "ok",
                "extraction_status": "complete",
                "returned": 1,
                "reported_total": 1,
            }
        ],
    }
    path = tmp_path / "envelope.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "VALIDATION_RUNS_DIR", tmp_path)

    rows = coverage_builder._parse_validation_runs()

    assert rows["tjro_liame"]["status"] == "valid"
    assert rows["tjro_liame"]["access_status"] == "public"
    assert rows["tjro_liame"]["evidence"].endswith("/envelope.json")
