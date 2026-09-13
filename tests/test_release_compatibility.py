from __future__ import annotations

from pathlib import Path

from tools.audit_release_compatibility import build, render_markdown


def test_release_compatibility_audit_passes_catalog_guards() -> None:
    root = Path(__file__).resolve().parents[1]
    payload = build(
        root / "docs" / "registry" / "provider-catalog.full.json",
        generated_at="2026-09-02T00:00:00+00:00",
    )

    assert payload["audit_mode"] == "offline_read_only"
    assert payload["promotion_performed"] is False
    assert payload["summary"] == {"providers": 85, "passed": 85, "failed": 0, "runtime": 80}


def test_release_compatibility_markdown_exposes_external_gates() -> None:
    rendered = render_markdown(build(generated_at="2026-09-02T00:00:00+00:00"))

    assert "Aprovação jurídica" in rendered
    assert "Runtime" in rendered and "Bloqueado" in rendered
