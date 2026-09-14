from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from nanojuris import NanoJurisClient
from tools import build_canonical_coverage as canonical


def test_canonical_sources_match_their_schemas() -> None:
    for source, schema in (
        (canonical.AUTHORITY_SOURCE, canonical.AUTHORITY_SCHEMA),
        (canonical.MATRIX_SOURCE, canonical.MATRIX_SCHEMA),
    ):
        Draft202012Validator(json.loads(schema.read_text(encoding="utf-8"))).validate(
            json.loads(source.read_text(encoding="utf-8"))
        )


def test_provider_catalog_matches_its_published_schema() -> None:
    root = canonical.ROOT
    schema = json.loads(
        (root / "docs" / "registry" / "provider-catalog.schema.json").read_text(encoding="utf-8")
    )
    catalog = json.loads(
        (root / "docs" / "registry" / "provider-catalog.full.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(catalog)


def test_all_runtime_providers_and_judicial_authorities_are_covered() -> None:
    authorities = canonical._read(canonical.AUTHORITY_SOURCE)
    matrix = canonical._read(canonical.MATRIX_SOURCE)
    assert canonical.validate(authorities, matrix) == []
    runtime = {source.source for source in NanoJurisClient().list_sources()}
    assert runtime <= {cell["provider"] for cell in matrix["cells"] if cell.get("provider")}
    assert (
        sum(
            item["branch"] in canonical.JUDICIAL_BRANCHES and item["kind"] in {"court", "council"}
            for item in authorities["authorities"]
        )
        == 94
    )


def test_tre_family_expands_to_all_regional_authorities() -> None:
    matrix = canonical._read(canonical.MATRIX_SOURCE)
    authorities = {
        cell["authority_id"]
        for cell in matrix["cells"]
        if cell.get("provider") == "tre_sjur_jurisprudencia"
    }
    assert len(authorities) == 27


def test_canonical_projections_are_synchronized() -> None:
    assert all(
        path.exists() and path.read_text(encoding="utf-8") == content
        for path, content in canonical.outputs().items()
    )
