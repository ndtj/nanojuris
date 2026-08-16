"""Regression coverage for the safe documentation inventory."""

from __future__ import annotations

from tools.audit_documentation_inventory import build_report, tracked_documents


def test_inventory_covers_every_markdown_document() -> None:
    report = build_report()

    for path in tracked_documents():
        assert f"`{path.as_posix()}`" in report


def test_inventory_marks_provider_contracts_as_compatibility_copies() -> None:
    report = build_report()

    assert "`docs/source-contracts/tcu_jurisprudencia.md` | `compatibility_copy`" in report
    assert "`docs/providers/tcu_jurisprudencia/README.md` | `canonical`" in report
