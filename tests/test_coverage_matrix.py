from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris import build_degree_matrix
from nanojuris.coverage_matrix import (
    CoverageMatrix,
    CoverageMatrixValidationError,
    CoverageSurface,
)
from tools.build_degree_coverage import build


def test_matrix_has_cjpg_and_cjsg_for_all_state_tjs() -> None:
    matrix = build_degree_matrix()
    cjpg = matrix.filtered(collection="CJPG")
    cjsg = matrix.filtered(collection="CJSG")

    assert len(cjpg) == 27
    assert len(cjsg) == 27
    assert {item.authority for item in cjpg} == {item.authority for item in cjsg}
    assert all(item.degree == "first" for item in cjpg)
    assert all(item.degree == "second" for item in cjsg)
    assert {item.authority for item in cjsg if item.status == "implemented"} == {
        "TJAC",
        "TJAL",
        "TJAM",
        "TJBA",
        "TJDFT",
        "TJGO",
        "TJES",
        "TJMS",
        "TJMT",
        "TJPA",
        "TJPB",
        "TJPI",
        "TJPR",
        "TJRJ",
        "TJRS",
        "TJSC",
        "TJTO",
        "TJRN",
        "TJRR",
        "TJRO",
        "TJCE",
        "TJPE",
        "TJSP",
        "TJSE",
        "TJMG",
    }


def test_matrix_rejects_invalid_collection_degree() -> None:
    with pytest.raises(CoverageMatrixValidationError, match="CJPG exige"):
        CoverageSurface(
            authority="TJSP",
            branch="state",
            degree="second",
            collection="CJPG",
            status="candidate",
            required=True,
        )
    with pytest.raises(CoverageMatrixValidationError, match="CJSG exige"):
        CoverageSurface(
            authority="TJSP",
            branch="state",
            degree="first",
            collection="CJSG",
            status="candidate",
            required=True,
        )


def test_summary_exposes_branch_degree_and_gaps() -> None:
    summary = build_degree_matrix().summary()

    assert summary["by_collection"]["CJPG"]["expected"] == 27
    assert summary["by_collection"]["CJSG"]["expected"] == 27
    assert summary["by_degree"]["first"] >= 27
    assert summary["by_degree"]["second"] >= 27
    assert summary["gap_count"] > 0
    assert summary["by_branch"]["electoral"] > 0
    assert summary["by_branch"]["military"] > 0
    assert summary["by_branch"]["labor"] > 0


def test_tjgo_projudi_covers_both_degree_bindings() -> None:
    matrix = build_degree_matrix()

    tjgo_cjpg = matrix.filtered(authority="TJGO", collection="CJPG")[0]
    tjgo_cjsg = matrix.filtered(authority="TJGO", collection="CJSG")[0]
    assert tjgo_cjpg.status == "implemented"
    assert tjgo_cjsg.status == "implemented"
    assert tjgo_cjpg.queryable
    assert tjgo_cjsg.queryable


def test_tjro_general_textual_surface_is_reconciled_without_degree_claim() -> None:
    matrix = build_degree_matrix()

    rows = matrix.filtered(authority="TJRO", collection="JURISPRUDENCIA")
    assert len(rows) == 1
    assert rows[0].provider == "tjro_jurisprudencia"
    assert rows[0].status == "implemented"
    assert rows[0].queryable is True
    assert rows[0].required is False


def test_tjro_cjsg_binds_textual_provider_not_contextual_liame() -> None:
    matrix = build_degree_matrix()

    rows = matrix.filtered(authority="TJRO", collection="CJSG")
    assert len(rows) == 1
    assert rows[0].provider == "tjro_jurisprudencia"
    assert rows[0].status == "implemented"
    assert rows[0].queryable is True
    assert "textual" in rows[0].notes


def test_candidate_degree_surface_preserves_current_live_evidence() -> None:
    matrix = build_degree_matrix()
    tjmg = matrix.filtered(authority="TJMG", collection="CJSG")[0]

    assert tjmg.provider == "tjmg_dspace_jurisprudencia"
    assert tjmg.degree == "second"
    assert "tjmg-dspace-jurisprudencia-live-20260906.json" in " ".join(tjmg.evidence_ids)


def test_tjmg_cjpg_route_keeps_captcha_as_access_controlled_evidence() -> None:
    matrix = build_degree_matrix()
    tjmg = matrix.filtered(authority="TJMG", collection="CJPG")[0]

    assert tjmg.status == "candidate"
    assert tjmg.provider is None
    assert "tjmg-cjpg-sentenca-route-live-20260909.json" in " ".join(tjmg.evidence_ids)


def test_tjma_degree_surfaces_preserve_captcha_boundary_evidence() -> None:
    matrix = build_degree_matrix()

    for collection in ("CJPG", "CJSG"):
        surface = matrix.filtered(authority="TJMA", collection=collection)[0]
        assert surface.status == "candidate"
        assert surface.provider is None
        assert "tjma-jurisprudence-route-live-20260908.json" in " ".join(surface.evidence_ids)


def test_tjrs_cjpg_route_evidence_does_not_claim_first_degree_coverage() -> None:
    matrix = build_degree_matrix()
    tjrs = matrix.filtered(authority="TJRS", collection="CJPG")[0]

    assert tjrs.status == "candidate"
    assert tjrs.provider is None
    assert tjrs.queryable is False
    assert "tjrs-cjpg-route-live-20260909.json" in " ".join(tjrs.evidence_ids)


def test_tjsc_cjpg_portal_shell_does_not_bind_second_degree_adapter() -> None:
    matrix = build_degree_matrix()
    tjsc = matrix.filtered(authority="TJSC", collection="CJPG")[0]

    assert tjsc.status == "candidate"
    assert tjsc.provider is None
    assert tjsc.queryable is False
    assert "tjsc-cjpg-route-live-20260909.json" in " ".join(tjsc.evidence_ids)


def test_tjdft_cjpg_contextual_search_does_not_bind_first_degree_adapter() -> None:
    matrix = build_degree_matrix()
    tjdft = matrix.filtered(authority="TJDFT", collection="CJPG")[0]

    assert tjdft.status == "candidate"
    assert tjdft.provider is None
    assert tjdft.queryable is False
    assert "tjdft-cjpg-route-live-20260909.json" in " ".join(tjdft.evidence_ids)


def test_matrix_contains_explicit_first_degree_unit_gaps() -> None:
    matrix = build_degree_matrix()

    gaps = {item.authority for item in matrix.gaps}
    assert "FEDERAL_FIRST_DEGREE_UNITS" in gaps
    assert "LABOR_FIRST_DEGREE_UNITS" in gaps
    assert "ELECTORAL_FIRST_DEGREE_UNITS" in gaps
    assert "MILITARY_FIRST_DEGREE_UNITS" in gaps


def test_electoral_metadata_provider_does_not_count_as_decision_search() -> None:
    matrix = build_degree_matrix()
    tse = matrix.filtered(authority="TSE", collection="SJUR")
    assert len(tse) == 1
    assert tse[0].status == "pending_contract"
    assert tse[0].queryable is False


def test_matrix_lists_all_tres_as_second_degree_surfaces() -> None:
    matrix = build_degree_matrix()
    tre_rows = tuple(
        surface
        for surface in matrix.filtered(branch="electoral", degree="second", collection="SJUR")
        if surface.scope == "tribunal"
    )
    authorities = {surface.authority for surface in tre_rows}
    assert len(authorities) == 27
    assert "TRESP" in authorities
    assert all(surface.status == "pending_contract" for surface in tre_rows)


def test_degree_matrix_artifact_matches_builder() -> None:
    root = Path(__file__).resolve().parents[1]
    artifact = json.loads(
        (root / "docs" / "topology" / "degree-coverage-matrix-20260901.json").read_text(
            encoding="utf-8"
        )
    )

    assert artifact == build()
    assert artifact["schema_version"] == "national-degree-coverage-matrix-v1"
    assert artifact["summary"]["by_collection"]["CJPG"]["expected"] == 27
    assert artifact["summary"]["by_collection"]["CJSG"]["expected"] == 27


def test_matrix_validation_rejects_duplicate_surface_ids() -> None:
    surface = CoverageSurface(
        authority="TJSP",
        branch="state",
        degree="first",
        collection="CJPG",
        status="candidate",
        required=True,
    )
    duplicate = CoverageMatrix(
        version="v1",
        generated_at="2026-09-01",
        surfaces=(surface, surface),
    )
    with pytest.raises(CoverageMatrixValidationError, match="surface_id duplicado"):
        duplicate.validate()
