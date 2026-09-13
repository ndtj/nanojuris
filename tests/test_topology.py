from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris import COURTS, packaged_topology
from nanojuris.topology import (
    CoverageClaim,
    CoverageEpoch,
    CoverageGap,
    CoverageProjection,
    NationalTopology,
    TopologyCollection,
    TopologyValidationError,
    project_coverage,
    topology_from_courts,
)
from tools.build_national_coverage import build as build_coverage
from tools.build_national_coverage import markdown as render_coverage_markdown
from tools.build_national_topology import build


def test_packaged_topology_reconciles_unbound_catalog_sources_explicitly() -> None:
    topology = packaged_topology()
    topology.validate()

    provider_ids = {
        provider for collection in topology.collections for provider in collection.provider_ids
    }
    assert len(topology.collections) >= 27
    assert "stf_juris" in provider_ids
    assert any(
        collection.authority_id == "authority:unknown"
        and collection.status == "unknown"
        and "bnp_pangea" in collection.provider_ids
        for collection in topology.collections
    )


def test_topology_ids_do_not_depend_on_portal_hostname() -> None:
    first = topology_from_courts(topology_version="v1", cutoff_date="2026-09-01")
    second = topology_from_courts(topology_version="v1", cutoff_date="2026-09-01")

    assert [item.collection_id for item in first.collections] == [
        item.collection_id for item in second.collections
    ]
    assert first.epochs[0].epoch_id == "v1@2026-09-01"


def test_coverage_epoch_and_claim_are_finite_and_explicit() -> None:
    epoch = CoverageEpoch.create("topology-v1", "2026-09-01")
    claim = CoverageClaim(
        epoch_id=epoch.epoch_id,
        dimension="provider",
        numerator=3,
        denominator=4,
        measured_at="2026-09-01",
    )

    assert claim.ratio == 0.75
    assert claim.to_dict()["ratio"] == 0.75


def test_invalid_claim_does_not_allow_fake_completeness() -> None:
    with pytest.raises(ValueError, match="numerator"):
        CoverageClaim(
            epoch_id="v1@2026-09-01",
            dimension="collection",
            numerator=5,
            denominator=4,
            measured_at="2026-09-01",
        )


def test_topology_rejects_duplicate_collections_and_mismatched_epochs() -> None:
    collection = TopologyCollection(
        collection_id="collection:test",
        authority_id="authority:test",
        branch="state",
        degree="second",
    )
    with pytest.raises(TopologyValidationError, match="collection_id duplicado"):
        NationalTopology(
            schema_version="v1",
            topology_version="topology-v1",
            collections=(collection, collection),
        ).validate()
    with pytest.raises(TopologyValidationError, match="outra topologia"):
        NationalTopology(
            schema_version="v1",
            topology_version="topology-v1",
            epochs=(CoverageEpoch.create("topology-v2", "2026-09-01"),),
        ).validate()


def test_projection_generates_claims_gaps_and_finite_history() -> None:
    projection = project_coverage(packaged_topology())
    claims = {claim.dimension: claim for claim in projection.claims}

    assert set(claims) == {"collection", "authority", "branch", "surface", "provider"}
    assert (claims["collection"].numerator, claims["collection"].denominator) == (19, 94)
    assert (claims["authority"].numerator, claims["authority"].denominator) == (19, 94)
    assert claims["provider"].numerator < claims["provider"].denominator
    assert projection.epoch.epoch_id in {epoch.epoch_id for epoch in projection.history}
    assert projection.gaps
    assert all(gap.status != "implemented" for gap in projection.gaps)
    assert projection.summary["gaps_by_branch"]["electoral"] == 27
    assert projection.summary["unreconciled_provider_count"] == 58


def test_projection_rejects_duplicate_dimensions_and_gap_ids() -> None:
    epoch = CoverageEpoch.create("topology-v1", "2026-09-01")
    claim = CoverageClaim(
        epoch_id=epoch.epoch_id,
        dimension="provider",
        numerator=1,
        denominator=2,
        measured_at="2026-09-01",
    )
    gap = CoverageGap(
        collection_id="collection:test",
        authority_id="authority:test",
        branch="state",
        status="candidate",
        reason="awaiting_contract",
    )
    with pytest.raises(TopologyValidationError, match="dimension duplicada"):
        CoverageProjection(epoch, (claim, claim), (gap,), (epoch,)).validate()
    with pytest.raises(TopologyValidationError, match="collection duplicada"):
        CoverageProjection(epoch, (claim,), (gap, gap), (epoch,)).validate()


def test_versioned_topology_artifact_matches_offline_builder() -> None:
    root = Path(__file__).resolve().parents[1]
    artifact = json.loads(
        (root / "docs" / "topology" / "national-topology.json").read_text(encoding="utf-8")
    )

    assert artifact == build()
    assert artifact["schema_version"] == "national-jurisprudence-topology-v1"
    assert artifact["metadata"]["network_access"] == "not_used"
    assert artifact["metadata"]["authority_count"] == 94
    assert artifact["metadata"]["authority_register_evidence"].endswith(
        "cnj-tribunal-register-20260901.json"
    )


def test_versioned_coverage_artifact_matches_offline_builder() -> None:
    root = Path(__file__).resolve().parents[1]
    artifact = json.loads(
        (root / "docs" / "topology" / "national-coverage-claims-20260901.json").read_text(
            encoding="utf-8"
        )
    )

    assert artifact == build_coverage()
    assert artifact["schema_version"] == "national-jurisprudence-coverage-v1"
    assert artifact["summary"]["network_access"] == "not_used"


def test_coverage_markdown_points_to_the_selected_machine_artifact() -> None:
    payload = build_coverage()
    rendered = render_coverage_markdown(payload, source_name="coverage.json")

    assert "Fonte machine-readable: `coverage.json`." in rendered
    assert "national-coverage-claims-20260901.json" not in rendered


def test_cnj_register_snapshot_is_reconciled_into_the_catalog() -> None:
    root = Path(__file__).resolve().parents[1]
    register = json.loads(
        (root / "docs" / "topology" / "cnj-tribunal-register-20260901.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(COURTS) == 94
    assert register["response_status"] == 200
    assert register["counts_observed"]["tribunais_regionais_eleitorais"] == 27
    assert register["counts_observed"]["tribunais_de_justica_militar_estaduais"] == 3
    assert len([court for court in COURTS if court.code.startswith("TRE")]) == 27
    assert {
        court.code
        for court in COURTS
        if court.branch == "military" and court.code.startswith("TJM")
    } == {
        "TJMMG",
        "TJMSP",
        "TJMRS",
    }
