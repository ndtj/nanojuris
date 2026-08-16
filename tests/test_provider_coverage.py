from __future__ import annotations

import json
from pathlib import Path

from nanojuris.client import NanoJurisClient
from tools.build_provider_coverage import build_catalog, render_docs

ROOT = Path(__file__).resolve().parents[1]


def test_provider_coverage_catalog_is_current() -> None:
    catalog_path = ROOT / "docs" / "registry" / "provider-catalog.full.json"
    expected = build_catalog()
    actual = json.loads(catalog_path.read_text(encoding="utf-8"))

    assert actual == expected


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
        source_id
        for source_id, entry in entries.items()
        if entry["lifecycle"] == "implemented"
    }

    assert implemented == runtime_sources

    for source_id in runtime_sources:
        entry = entries[source_id]
        assert entry["documentation"]["human_doc"] == f"docs/providers/{source_id}/README.md"
        assert entry["input_contract"]["search_modes"] == (
            entry["source_contract"]["evidence"]["search_modes"]
        )
        assert entry["output_contract"]["canonical_records"] == (
            entry["source_contract"]["evidence"]["canonical_records"]
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
