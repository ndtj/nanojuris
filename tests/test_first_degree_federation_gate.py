from __future__ import annotations

import json
from pathlib import Path

from tools.audit_first_degree_federation import audit

ROOT = Path(__file__).resolve().parents[1]


def _load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_first_degree_gate_matches_generated_sources() -> None:
    result = audit(
        _load("docs/coverage/surface-state-registry-20260902.json"),
        _load("docs/registry/provider-catalog.full.json"),
        _load("docs/operations/technical-promotion-manifest-20260905.json"),
    )
    assert result["summary"]["errors"] == 0
    assert result["summary"]["cjpg_surfaces"] == 27
    assert result["summary"]["federated"] >= 1
    assert all(
        row["state"] == "federated"
        for row in result["surfaces"]
        if row["federation_status"] == "enabled"
    )


def test_cjpg_gaps_are_not_claimed_as_federated() -> None:
    result = audit(
        _load("docs/coverage/surface-state-registry-20260902.json"),
        _load("docs/registry/provider-catalog.full.json"),
        _load("docs/operations/technical-promotion-manifest-20260905.json"),
    )
    assert all(
        row["federation_status"] != "enabled" or row["state"] == "federated"
        for row in result["surfaces"]
    )
