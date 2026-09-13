from __future__ import annotations

import json
from pathlib import Path

from tools.build_national_coverage_gap_map import build

ROOT = Path(__file__).resolve().parents[1]


def test_national_gap_map_covers_every_matrix_surface() -> None:
    report = build()
    assert report["summary"]["surfaces"] == 249
    assert report["summary"]["core_surfaces"] == 155
    assert report["summary"]["conditional_surfaces"] == 94
    # The federal eproc detail smoke now closes one additional gold gate while
    # retaining all external blocks as explicit non-ready rows.
    assert report["summary"]["core_ready_state"] == 68
    assert report["summary"]["core_unready"] == 87
    assert report["summary"]["catalog_providers"] == 85
    # Curated TRT3 ementario is cataloged as an additional contextual surface;
    # catalog orphan accounting remains explicit and non-promotional.
    assert report["summary"]["catalog_orphans"] == 24
    assert report["summary"]["gold_gate_complete"] == 68
    assert report["summary"]["catalog_orphan_gold_gate_complete"] == 2
    assert report["summary"]["discovery_queue"] == 181
    assert report["summary"]["providerless_core"] == 46
    assert report["summary"]["providerless_conditional"] == 92
    assert len(report["surfaces"]) == report["summary"]["surfaces"]
    assert len(report["discovery_queue"]) == report["summary"]["discovery_queue"]
    assert all(
        set(item)
        >= {
            "surface_id",
            "authority",
            "branch",
            "degree",
            "collection",
            "batch",
            "current_state",
            "gate_gaps",
            "next_action",
        }
        for item in report["discovery_queue"]
    )
    assert all(
        "gate_gaps" in item
        and "missing_information" in item
        and "gold_gates" in item
        and "blockers" in item
        for item in report["surfaces"]
    )
    assert len(report["provider_orphans"]) == report["summary"]["catalog_orphans"]
    assert all(item["row_kind"] == "catalog_orphan" for item in report["provider_orphans"])
    assert all("gold_gates" in item and "blockers" in item for item in report["provider_orphans"])
    matrix_providers = {item["provider"] for item in report["surfaces"] if item.get("provider")}
    catalog_reconciled = matrix_providers | {
        item["provider"] for item in report["provider_orphans"]
    }
    assert len(catalog_reconciled) == report["summary"]["catalog_providers"]


def test_gap_map_keeps_blocked_sources_explicit() -> None:
    report = build()
    blocked = [
        item for item in report["surfaces"] if item["current_state"] == "blocked_or_unavailable"
    ]
    # The same reconciliation makes the current TRF1 access-control state
    # explicit in the national gap map instead of hiding it as discovery.
    assert len(blocked) == 12
    assert all(item["workstream"] == "blocked_recheck_or_official_alternative" for item in blocked)
    assert all(not item["gold_gates"]["live_validated"] for item in blocked)
    assert all("live_validated" in item["blockers"] for item in blocked)
    for authority in ("TRT3", "TRT4"):
        row = next(item for item in blocked if item["authority"] == authority)
        assert row["collection"] == "JURISPRUDENCIA"
        assert row["live_status"] == "access_blocked"
        assert row["official_entry_point"]
        assert row["evidence_ids"]


def test_tre_rows_use_executable_family_without_federation_claim() -> None:
    report = build()
    row = next(
        item
        for item in report["surfaces"]
        if item["authority"] == "TRESP" and item["collection"] == "SJUR"
    )
    assert row["provider"] == "tre_sjur_jurisprudencia"
    assert row["current_state"] == "contract_pending"
    assert row["live_status"] == "valid"
    assert row["federation_status"] == "not_enabled"
    assert row["gold_gates"]["degree_contract"] is False


def test_tse_sjur_row_uses_textual_runtime_provider_without_promotion() -> None:
    report = build()
    row = next(
        item
        for item in report["surfaces"]
        if item["authority"] == "TSE" and item["collection"] == "SJUR"
    )
    assert row["provider"] == "tse_sjur_jurisprudencia"
    assert row["degree"] == "superior"
    assert row["instance"] == "superior"
    assert row["current_state"] == "contract_pending"
    assert row["live_status"] == "valid"
    assert row["federation_status"] == "not_enabled"


def test_trt8_live_surface_is_bound_and_technically_promoted() -> None:
    report = build()
    row = next(
        item
        for item in report["surfaces"]
        if item["authority"] == "TRT8"
        and item["branch"] == "labor"
        and item["degree"] == "second"
        and item["collection"] == "JURISPRUDENCIA"
    )
    assert row["provider"] == "trt8_pje_jurisprudencia"
    assert row["current_state"] == "federated_live"
    assert row["live_status"] == "valid"
    assert row["federation_status"] == "enabled"
    assert row["evidence_ids"]


def test_state_rollup_is_exactly_the_27_court_cjpg_cjsg_scope() -> None:
    report = build()
    rollup = report["state_authorities"]
    assert report["summary"]["state_authorities"] == 27
    assert len(rollup) == 27
    assert set(rollup) == {
        "TJAC",
        "TJAL",
        "TJAM",
        "TJAP",
        "TJBA",
        "TJCE",
        "TJDFT",
        "TJES",
        "TJGO",
        "TJMA",
        "TJMG",
        "TJMS",
        "TJMT",
        "TJPA",
        "TJPB",
        "TJPE",
        "TJPI",
        "TJPR",
        "TJRJ",
        "TJRN",
        "TJRO",
        "TJRR",
        "TJRS",
        "TJSC",
        "TJSE",
        "TJSP",
        "TJTO",
    }
    assert report["summary"]["state_cjsg_gold_ready"] == 25
    assert report["summary"]["state_cjpg_gold_ready"] == 8
    assert report["summary"]["state_authorities_with_both_gold_tracks"] == 7
    assert all(
        set(item) >= {"cjpg", "cjsg", "missing_tracks", "next_actions"} for item in rollup.values()
    )
    # A discovered-but-unimplemented first-degree route is explicit, never an
    # authoritative empty result.
    assert rollup["TJBA"]["cjpg"]["state"] == "discovery_pending"
    assert rollup["TJBA"]["cjpg"]["provider"] is None
    assert rollup["TJBA"]["cjpg"]["live_status"] == "not_observed"
    assert "runtime" in rollup["TJBA"]["cjpg"]["blockers"]

    # TJAL ESMAL is a technically federated, explicitly partial CJPG source.
    # It improves live recall without being confused with an exhaustive
    # first-instance corpus (the source reports no authoritative total).
    assert rollup["TJAL"]["cjpg"]["provider"] == "tjal_esmal_banco_sentencas"
    assert rollup["TJAL"]["cjpg"]["state"] == "federated_live"


def test_generic_federal_surfaces_are_explicitly_aliased_to_eproc() -> None:
    report = build()
    expected = {
        "TRF2": "trf2_eproc_jurisprudencia",
        "TRF4": "trf4_eproc_jurisprudencia",
        "TRF6": "trf6_eproc_jurisprudencia",
    }
    for authority, provider in expected.items():
        row = next(
            item
            for item in report["surfaces"]
            if item["authority"] == authority
            and item["branch"] == "federal"
            and item["degree"] == "second"
            and item["collection"] == "JURISPRUDENCIA"
        )
        assert row["provider"] == provider
        assert row["current_state"] == "federated_live"
        assert row["source_class"] == "official_court_jurisprudence_alias"
        assert row["coverage_alias_of"] == [
            f"surface:{authority.lower()}:eproc:second:{provider.replace('_', '-')}"
        ]

    tnu = next(
        item
        for item in report["surfaces"]
        if item["authority"] == "TNU"
        and item["branch"] == "federal"
        and item["degree"] == "superior"
        and item["collection"] == "PORTAL"
    )
    assert tnu["provider"] == "tnu_eproc_jurisprudencia"
    assert tnu["current_state"] == "federated_live"
    assert tnu["source_class"] == "official_court_jurisprudence_alias"
    assert tnu["coverage_alias_of"] == ["surface:tnu:eproc:superior:tnu-eproc-jurisprudencia"]


def test_trf1_gap_uses_the_existing_cjf_adapter_and_preserves_blocked_state() -> None:
    report = build()
    row = next(
        item
        for item in report["surfaces"]
        if item["authority"] == "TRF1"
        and item["branch"] == "federal"
        and item["degree"] == "second"
        and item["collection"] == "JURISPRUDENCIA"
    )
    assert row["provider"] == "cjf_jurisprudencia"
    assert row["current_state"] == "blocked_or_unavailable"
    assert row["gold_gates"]["runtime"] is True
    assert row["gold_gates"]["live_validated"] is False


def test_superior_and_military_authorities_keep_canonical_branches() -> None:
    matrix = json.loads(
        (
            ROOT
            / "specs"
            / "changes"
            / "0098-national-jurisprudence-gold-coverage"
            / "national-source-task-matrix.json"
        ).read_text(encoding="utf-8")
    )
    rows = matrix["rows"]
    stj = [row for row in rows if row["authority"] == "STJ" and row["collection"] == "PORTAL"]
    stm = [row for row in rows if row["authority"] == "STM" and row["collection"] == "PORTAL"]
    assert len(stj) == 1
    assert stj[0]["branch"] == "superior"
    assert stj[0]["provider"] == "stj_scon"
    assert len(stm) == 1
    assert stm[0]["branch"] == "military"
    assert stm[0]["provider"] == "stm_jurisprudencia"
