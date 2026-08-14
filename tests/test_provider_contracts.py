from __future__ import annotations

from nanojuris import NanoJurisClient
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


def test_unified_search_is_explicitly_opted_into_each_agent_interface():
    client = NanoJurisClient()

    for capability in client.list_sources():
        if not capability.supports_unified_search:
            continue

        assert capability.category in JURISPRUDENCE_CATEGORIES
        assert capability.supports_cli is True
        assert capability.supports_mcp is True
        assert capability.supports_studio is True


def test_default_unified_search_includes_curated_jurisprudence_sources():
    client = NanoJurisClient()

    sources = set(client._default_unified_sources())

    assert {"cnj_jurisprudencia", "tjce_informativos"}.issubset(sources)
