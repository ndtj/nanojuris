from __future__ import annotations

import json
from pathlib import Path

from nanojuris import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.routing import JURISPRUDENCE_CATEGORIES


def test_every_registered_provider_declares_a_complete_minimum_contract():
    client = NanoJurisClient()
    names = sorted(client.providers)
    capabilities = client.list_sources()

    assert names == sorted(capability.source for capability in capabilities)
    assert len(names) == len(set(names))

    for name, provider in sorted(client.providers.items()):
        capability = provider.get_capabilities()

        assert capability.source == name
        assert capability.display_name.strip()
        assert capability.source_url.startswith(("http://", "https://"))
        assert capability.category.strip()
        assert capability.search_modes
        assert capability.document_types
        assert capability.content_formats
        assert capability.canonical_records
        assert capability.extracted_fields
        assert capability.access_statuses
        assert capability.endpoints
        assert capability.limitations
        assert capability.responsible_use


def test_unified_search_capability_is_independent_from_agent_interfaces():
    client = NanoJurisClient()

    for capability in client.list_sources():
        if not capability.supports_unified_search:
            continue

        assert capability.category in JURISPRUDENCE_CATEGORIES


def test_default_unified_search_keeps_opt_in_curated_sources_explicit():
    client = NanoJurisClient()

    sources = set(client._default_unified_sources())

    assert "cnj_jurisprudencia" in sources
    assert "tjce_informativos" not in sources

    opted_in = NanoJurisClient(NanoJurisConfig(unified_opt_in_sources=("tjce_informativos",)))
    assert "tjce_informativos" in opted_in._default_unified_sources()


def test_default_federation_matches_technical_promotion_manifest():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (root / "docs" / "operations" / "technical-promotion-manifest-20260905.json").read_text(
            encoding="utf-8"
        )
    )
    client_sources = set(NanoJurisClient()._default_unified_sources())
    enabled = set(manifest["summary"]["enabled_sources"])
    blocked = {row["source"] for row in manifest["decisions"] if row["mode"] == "blocked"}

    assert client_sources == enabled
    assert client_sources.isdisjoint(blocked)
