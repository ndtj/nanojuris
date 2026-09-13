"""Regression checks for the independent NanoJuris/Juscraper bindings."""

from __future__ import annotations

import json
from pathlib import Path

from nanojuris import NanoJurisClient
from nanojuris.providers.tjpb_pje_jurisprudencia import TjpbPjeJurisprudenciaProvider

ROOT = Path(__file__).resolve().parents[1]
# Consume the regenerated current artifact so parity assertions exercise the
# same crosswalk that is used by the coverage reports.  A dated snapshot can
# remain as historical evidence, but must not hide regressions in the live
# mapping (for example, TJTO exposes both CJPG and CJSG through one route).
DIFF = ROOT / "docs" / "provider-discovery" / "juscraper-semantic-diff-current.json"
UPSTREAM_TEST_RUN = (
    ROOT / "docs" / "provider-discovery" / "juscraper-contract-test-run-20260906.json"
)


def test_every_covered_juscraper_surface_has_a_registered_nanojuris_binding() -> None:
    payload = json.loads(DIFF.read_text(encoding="utf-8"))
    covered = [
        row
        for row in payload["records"]
        if row.get("status") == "covered_requires_differential_fixture"
    ]
    client = NanoJurisClient()
    missing = sorted(
        {
            str(row["nanojuris_equivalent"])
            for row in covered
            if row.get("nanojuris_equivalent") not in client.providers
        }
    )
    assert missing == []


def test_juscraper_parity_never_promotes_unmatched_candidates() -> None:
    payload = json.loads(DIFF.read_text(encoding="utf-8"))
    client = NanoJurisClient()
    candidates = [row for row in payload["records"] if row.get("status") == "no_runtime_equivalent"]
    assert all(
        row.get("nanojuris_equivalent") is None
        or row["nanojuris_equivalent"] not in client.providers
        for row in candidates
    )
    blocked = {
        row["nanojuris_equivalent"]
        for row in payload["records"]
        if row.get("status") == "runtime_overlap_blocked"
    }
    # TJAP still has no tokenless route. TJMG's current inventory points to
    # the court's separate modern public API, which is a distinct public
    # contract from Juscraper's legacy form and is therefore not blocked here.
    assert "tjap_tucujuris" in blocked
    assert "tjmg_jurisprudencia" not in blocked
    assert "tjap_tucujuris" not in client.providers
    assert "tjmg_jurisprudencia" in client.providers


def test_upstream_candidate_contracts_are_recorded_without_false_live_promotion() -> None:
    payload = json.loads(UPSTREAM_TEST_RUN.read_text(encoding="utf-8"))

    assert payload["result"] == {
        "passed": 43,
        "failed": 0,
        "skipped": 0,
        "environment": "temporary checkout with test dependencies",
    }
    assert "Turnstile" in payload["live_boundaries"]["tjap"]
    assert "CAPTCHA" in payload["live_boundaries"]["tjmg"]


def test_tjpb_pje_declares_translated_and_terminal_filter_semantics() -> None:
    capabilities = TjpbPjeJurisprudenciaProvider().get_capabilities()

    assert capabilities.filter_status("case_class") == "translated"
    assert capabilities.filter_status("degree") == "native"
    assert capabilities.filter_status("party_name") == "unsupported"
    assert capabilities.filter_status("updated_from") == "unsupported"
    assert capabilities.filter_status("authority") == "validated_scope"
    assert capabilities.filter_status("courts") == "unsupported"
    assert capabilities.filter_status("document_type") == "translated"


def test_juscraper_tjto_cjpg_keeps_the_proven_nanojuris_binding() -> None:
    payload = json.loads(DIFF.read_text(encoding="utf-8"))
    row = next(
        item
        for item in payload["records"]
        if item["source_id"] == "tjto" and item["surface"] == "cjpg"
    )
    assert row["nanojuris_equivalent"] == "tjto_jurisprudencia"
    assert row["status"] == "covered_requires_differential_fixture"
