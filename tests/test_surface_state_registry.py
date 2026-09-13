from __future__ import annotations

import json
from pathlib import Path

from tools.build_surface_state_registry import build  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_surface_registry_covers_every_matrix_surface() -> None:
    payload = build()
    # TJRO generic jurisprudence is an explicit mixed-degree surface in the
    # 2026-09-02 matrix; it must remain represented even though it does not
    # claim CJPG/CJSG coverage.
    assert payload["summary"]["surface_count"] == 151
    assert payload["summary"]["required_surface_count"] == 125
    ids = [item["surface_id"] for item in payload["surfaces"]]
    assert len(ids) == len(set(ids))
    assert payload["summary"]["cjpg"] == {"implemented": 9, "expected": 27}
    # The matrix counts only explicitly contracted CJSG bindings. Generic or
    # blocked routes stay outside this denominator; the state registry keeps
    # that distinction instead of inferring coverage.
    assert payload["summary"]["cjsg"] == {"implemented": 25, "expected": 27}


def test_surface_registry_keeps_contract_live_and_federation_independent() -> None:
    payload = build()
    by_id = {item["surface_id"]: item for item in payload["surfaces"]}

    tjes_cjpg = by_id["surface:tjes:cjpg:first:tjes-cjpg"]
    assert tjes_cjpg["lifecycle"] == "implemented"
    assert tjes_cjpg["contract_status"] in {"implemented_local", "live_validated"}
    assert tjes_cjpg["federation_status"] == "enabled"
    assert tjes_cjpg["legal_status"] == "operator_approved"

    tjrn_cjsg = by_id["surface:tjrn:cjsg:second:tjrn-jurisprudencia"]
    assert tjrn_cjsg["lifecycle"] == "implemented"
    # TJRN now has an explicit appellate binding backed by bounded live
    # degree=second evidence; its first-degree row remains unproven.
    assert tjrn_cjsg["contract_status"] == "live_validated"
    assert tjrn_cjsg["federation_status"] == "enabled"

    tjro_cjsg = by_id["surface:tjro:cjsg:second:tjro-jurisprudencia"]
    assert tjro_cjsg["contract_status"] == "live_validated"
    assert tjro_cjsg["federation_status"] == "enabled"

    tjap_cjsg = by_id["surface:tjap:cjsg:second:tjap-tucujuris"]
    assert tjap_cjsg["contract_status"] == "blocked_access"
    assert tjap_cjsg["federation_status"] == "blocked"


def test_surface_registry_reconciles_operator_technical_promotion() -> None:
    payload = build()
    by_id = {item["surface_id"]: item for item in payload["surfaces"]}

    # The promotion manifest is the generated source of truth for the
    # operator's "all technically ready" decision; this must not leak to a
    # candidate or a blocked source.
    assert by_id["surface:tjpi:portal:second:tjpi-juspi"]["legal_status"] == "operator_approved"
    assert (
        by_id["surface:tjrn:jurisprudencia:mixed:tjrn-jurisprudencia"]["legal_status"]
        == "operator_approved"
    )
    assert (
        by_id["surface:tjap:cjsg:second:tjap-tucujuris"]["legal_status"] == "pending_human_review"
    )


def test_surface_registry_does_not_federate_capability_only_sources() -> None:
    payload = build()
    by_id = {item["surface_id"]: item for item in payload["surfaces"]}

    # STJ SCON remains diagnostic-only because it is incomplete.  TJAC has
    # since passed the technical gates for textual search and is now enabled;
    # its detail-level CAPTCHA is represented separately in live evidence.
    assert by_id["surface:stj:portal:superior:stj-scon"]["federation_status"] == "blocked"
    assert by_id["surface:tjac:cjsg:second:tjac-cjsg"]["federation_status"] == "enabled"


def test_surface_registry_preserves_diagnostic_evidence_for_tjma_gap() -> None:
    payload = build()
    tjma = next(
        item for item in payload["surfaces"] if item["surface_id"] == "surface:tjma:cjsg:second:gap"
    )
    assert tjma["provider"] is None
    assert tjma["diagnostic_provider"] == "tjma_jurisconsult"
    assert tjma["live_status"] == "access_controlled"
    assert tjma["federation_status"] == "not_enabled"
    assert any("tjma-jurisprudencia-captcha" in value for value in tjma["evidence_ids"])


def test_surface_registry_reconciles_cjf_trf1_without_claiming_live_coverage() -> None:
    payload = build()
    trf1 = next(
        item
        for item in payload["surfaces"]
        if item["authority"] == "TRF1"
        and item["branch"] == "federal"
        and item["degree"] == "second"
        and item["collection"] == "JURISPRUDENCIA"
    )
    assert trf1["provider"] == "cjf_jurisprudencia"
    assert trf1["contract_status"] == "blocked_access"
    assert trf1["live_status"] == "access_control_required"
    assert trf1["federation_status"] == "blocked"


def test_surface_registry_artifact_matches_builder() -> None:
    artifact = json.loads(
        (ROOT / "docs" / "coverage" / "surface-state-registry-20260902.json").read_text(
            encoding="utf-8"
        )
    )
    assert artifact == build()
    assert artifact["schema_version"] == "surface-state-registry-v1"


def test_surface_registry_schema_declares_independent_state_dimensions() -> None:
    schema = json.loads(
        (ROOT / "docs" / "schemas" / "surface-state-registry-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert schema["$defs"]["surface"]["required"][:6] == [
        "surface_id",
        "authority",
        "branch",
        "degree",
        "instance",
        "collection",
    ]
    required = set(schema["$defs"]["surface"]["required"])
    assert {
        "lifecycle",
        "contract_status",
        "live_status",
        "federation_status",
        "legal_status",
    } <= required


def test_surface_registry_reports_diagnostic_runtime_divergence() -> None:
    payload = build()
    assert payload["summary"]["divergence_count"] == 1
    assert payload["divergences"] == [
        {
            "surface_id": "surface:tjma:cjsg:second:gap",
            "kind": "diagnostic_evidence_without_runtime_binding",
            "diagnostic_provider": "tjma_jurisconsult",
        }
    ]
