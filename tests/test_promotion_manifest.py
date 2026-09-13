import json
from pathlib import Path

from nanojuris import NanoJurisClient
from tools.build_promotion_manifest import _load_legal_allowlist, build_manifest

ROOT = Path(__file__).resolve().parents[1]


def _catalog() -> dict:
    return json.loads(
        (ROOT / "docs" / "registry" / "provider-catalog.full.json").read_text(encoding="utf-8")
    )


def _row(manifest: dict, source: str) -> dict:
    return next(item for item in manifest["decisions"] if item["source"] == source)


def test_technical_gates_are_evaluated_without_mutating_federation() -> None:
    manifest = build_manifest(_catalog())
    tjes = _row(manifest, "tjes_cjpg")

    assert tjes["technical_gate"] is True
    assert tjes["mode"] == "opt_in"
    assert tjes["legal_gate"] is False
    assert tjes["operator_accepted"] is False
    assert "human_legal_reuse_gate_pending" in tjes["reasons"]
    assert tjes["default_federation_before"] is True


def test_explicit_legal_allowlist_enables_technically_ready_source() -> None:
    manifest = build_manifest(_catalog(), {"tjes_cjpg"})
    tjes = _row(manifest, "tjes_cjpg")

    assert tjes["technical_gate"] is True
    assert tjes["legal_gate"] is True
    assert tjes["operator_accepted"] is True
    assert tjes["mode"] == "enabled"
    assert manifest["summary"]["enabled_after_explicit_legal_approval"] >= 1


def test_operator_decision_enables_all_technical_ready_sources(tmp_path) -> None:
    path = tmp_path / "operator-approval.json"
    path.write_text(
        '{"operator_accepts_all_technically_ready": true, "approved_sources": []}',
        encoding="utf-8",
    )

    approvals = _load_legal_allowlist(path)
    manifest = build_manifest(_catalog(), approvals)

    assert "__all_technically_ready__" in approvals
    assert manifest["policy"]["operator_accepts_all_technically_ready"] is True
    assert (
        manifest["summary"]["enabled_after_operator_approval"]
        == manifest["summary"]["technical_ready"]
    )
    assert (
        manifest["summary"]["enabled_after_technical_operator_decision"]
        == manifest["summary"]["technical_ready"]
    )


def test_technical_ready_sources_are_in_runtime_federation() -> None:
    manifest = build_manifest(_catalog(), {"__all_technically_ready__"})
    runtime_sources = set(NanoJurisClient()._default_unified_sources())

    assert set(manifest["summary"]["enabled_sources"]) <= runtime_sources


def test_blocked_source_is_never_promoted() -> None:
    manifest = build_manifest(_catalog(), {"cjf_jurisprudencia"})
    tjto = _row(manifest, "cjf_jurisprudencia")

    assert tjto["mode"] == "blocked"
    assert tjto["technical_gate"] is False
    assert tjto["access_status"] in {"blocked_access", "blocked_transport"}


def test_opt_in_only_source_never_enters_default_enabled_sources() -> None:
    manifest = build_manifest(_catalog(), {"__all_technically_ready__"})
    row = _row(manifest, "tjsp_nugepnac")

    assert row["technical_gate"] is True
    assert row["opt_in_supported"] is True
    assert row["mode"] == "opt_in"
    assert "tjsp_nugepnac" not in manifest["summary"]["enabled_sources"]
