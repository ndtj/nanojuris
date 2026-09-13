from __future__ import annotations

from pathlib import Path

from tools.build_interface_impact import build, render_markdown


def test_interface_impact_matrix_is_complete_and_non_promotional() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = build(
        root / "docs" / "registry" / "provider-catalog.full.json",
        generated_at="2026-09-02T00:00:00+00:00",
    )

    assert payload["schema_version"] == 1
    assert payload["no_rollout_mutation"] is True
    assert payload["summary"]["providers"] == 85
    assert payload["summary"]["runtime"] == 80
    assert {item["source_id"] for item in payload["items"]}.__len__() == 85
    candidate = next(
        item for item in payload["items"] if item["source_id"] == "tjrn_jurisprudencia"
    )
    assert candidate["rollout_mode"] == "enabled"
    assert candidate["impact"]["unified_search"] is True


def test_interface_impact_markdown_has_all_surface_columns() -> None:
    payload = build(generated_at="2026-09-02T00:00:00+00:00")
    rendered = render_markdown(payload)

    assert "SDK" in rendered and "Federação" in rendered and "Exports" in rendered
    assert "`blocked`/`opt_in`" in rendered
