from __future__ import annotations

import json
from pathlib import Path

from tools.build_provider_capability_ledger import build, render_markdown
from tools.build_provider_capability_ledger import main as ledger_main

ROOT = Path(__file__).resolve().parents[1]


def test_ledger_reconciles_every_catalog_provider() -> None:
    ledger = build(ROOT)
    catalog = json.loads(
        (ROOT / "docs/registry/provider-catalog.full.json").read_text(encoding="utf-8")
    )
    ids = [row["source_id"] for row in ledger["providers"]]
    assert ledger["summary"]["providers"] == len(catalog["entries"])
    assert len(ids) == len(set(ids))
    assert set(ids) == {row["source_id"] for row in catalog["entries"]}
    assert ledger["summary"]["runtime"] == sum(
        row.get("implementation_status") == "runtime" for row in catalog["entries"]
    )


def test_ledger_preserves_terminal_filter_state() -> None:
    ledger = build(ROOT)
    row = next(row for row in ledger["providers"] if row["source_id"] == "bnp_pangea")
    filters = row["contract"]["filters"]
    assert filters["unverified"] == []
    assert filters["counts"]["native"] + filters["counts"]["unsupported"] == len(
        filters["verified"]
    )


def test_ledger_has_terminal_semantics_for_every_provider() -> None:
    ledger = build(ROOT)
    assert ledger["summary"]["unverified_filter_declarations"] == 0
    for row in ledger["providers"]:
        assert row["contract"]["filters"]["unverified"] == []


def test_ledger_markdown_is_a_diagnostic_not_a_coverage_claim() -> None:
    text = render_markdown(build(ROOT))
    assert "Unknown and blocked states are preserved" in text
    assert "27/27" not in text


def test_ledger_check_is_reproducible_without_timestamp_churn(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["build_provider_capability_ledger", "--check"])
    assert ledger_main() == 0
