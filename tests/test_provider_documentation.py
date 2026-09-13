from __future__ import annotations

import json
import sys
from pathlib import Path

from nanojuris.client import NanoJurisClient

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_provider_docs import audit, render  # noqa: E402


def test_every_provider_has_source_contract_dossier() -> None:
    provider_dir = ROOT / "src" / "nanojuris" / "providers"
    docs_dir = ROOT / "docs" / "source-contracts"

    providers = {
        path.stem for path in provider_dir.glob("*.py") if path.stem not in {"__init__", "base"}
    }
    dossiers = {path.stem for path in docs_dir.glob("*.md")}

    assert sorted(providers - dossiers) == []


def test_provider_development_queue_links_existing_candidate_dossiers() -> None:
    queue_path = ROOT / "docs" / "provider-development-queue.md"
    docs_dir = ROOT / "docs" / "source-contracts"

    expected_candidates = {
        "tjpi_juspi",
        "tjrr_juris",
        "tjmt_jurisprudencia_api",
        "tjpa_jurisprudencia_bff",
        "tjpb_pje_jurisprudencia",
    }

    queue = queue_path.read_text(encoding="utf-8")
    existing_dossiers = {path.stem for path in docs_dir.glob("*.md")}

    assert expected_candidates <= existing_dossiers
    for candidate in sorted(expected_candidates):
        assert f"providers/{candidate}/README.md" in queue


def test_every_documented_source_has_canonical_provider_directory() -> None:
    source_docs = ROOT / "docs" / "source-contracts"
    provider_docs = ROOT / "docs" / "providers"

    source_ids = {path.stem for path in source_docs.glob("*.md") if path.stem != "README"}

    assert source_ids
    for source_id in sorted(source_ids):
        canonical = provider_docs / source_id / "README.md"
        legacy = source_docs / f"{source_id}.md"
        assert canonical.is_file(), source_id
        assert legacy.is_file(), source_id
        assert canonical.read_bytes() == legacy.read_bytes(), source_id


def test_provider_registry_matches_documentation_and_runtime_inventory() -> None:
    registry_path = ROOT / "docs" / "registry" / "providers.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    source_docs = ROOT / "docs" / "source-contracts"

    implemented = set(registry["implemented"])
    candidates = set(registry["candidates"])
    runtime_providers = {capability.source for capability in NanoJurisClient().list_sources()}
    documented_sources = {path.stem for path in source_docs.glob("*.md") if path.stem != "README"}
    families = set(registry["families"])

    assert implemented == runtime_providers
    assert implemented.isdisjoint(candidates)
    assert implemented.isdisjoint(families)
    assert candidates.isdisjoint(families)
    assert implemented | candidates | families == documented_sources


def test_provider_documentation_audit_report_is_current() -> None:
    report_path = ROOT / "docs" / "provider-documentation-audit.md"
    template_path = ROOT / "docs" / "provider-dossier-template.md"
    registry_path = ROOT / "docs" / "registry" / "providers.json"

    assert template_path.is_file()
    assert report_path.read_text(encoding="utf-8") == render(audit())

    rows = audit()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    expected_sources = (
        set(registry["implemented"]) | set(registry["candidates"]) | set(registry["families"])
    )
    assert len(rows) == len(expected_sources)
    assert all(row["parity"] for row in rows)


def test_latest_platform_live_summary_has_redacted_route_inventory() -> None:
    summary_path = (
        ROOT / "docs" / "validation" / "runs" / "20260828T010539Z-platform-live-summary.json"
    )
    template_path = ROOT / "docs" / "validation" / "runs" / "playwright-live-run-template.md"

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    routes = summary["route_inventory"]
    paths = {route["path"] for route in routes}

    assert template_path.is_file()
    assert {
        "/auth/session",
        "/api/v1/sources",
        "/api/v1/search",
        "/bff/assistant",
        "/api/v1/admin/users",
        "/api/v1/admin/audit",
    } <= paths
    assert all("?" not in path and "#" not in path for path in paths)
    assert all(isinstance(status, int) for route in routes for status in route["statuses_observed"])
    assert "Nenhum cookie" in template_path.read_text(encoding="utf-8")
