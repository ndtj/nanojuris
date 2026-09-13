from __future__ import annotations

from tools.build_release_provenance import build, render_markdown


def test_release_provenance_has_sbom_and_explicit_legal_gate() -> None:
    payload = build(generated_at="2026-09-02T00:00:00+00:00")

    assert payload["bom"]["bomFormat"] == "CycloneDX"
    assert payload["provenance"]["source_catalog_entries"] == 85
    assert payload["provenance"]["runtime_providers"] == 80
    assert payload["provenance"]["redistribution_authorized"] is False
    assert payload["production_action_performed"] is False


def test_release_provenance_markdown_does_not_claim_redistribution() -> None:
    rendered = render_markdown(build(generated_at="2026-09-02T00:00:00+00:00"))

    assert "redistribuição autorizada: **não**" in rendered
    assert "SHA-256" in rendered
