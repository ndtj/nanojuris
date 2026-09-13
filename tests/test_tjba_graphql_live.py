from __future__ import annotations

import os
from urllib.parse import urlparse

import pytest

from nanojuris import NanoJurisClient, NanoJurisConfig

pytestmark = pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_LIVE") != "1",
    reason="Set NANOJURIS_RUN_LIVE=1 to query live public sources",
)


@pytest.mark.live
def test_live_tjba_search_and_public_full_text():
    client = NanoJurisClient(config=NanoJurisConfig(timeout=45, rate_limit_interval=0.5))

    page = client.search("dano moral", source="tjba_graphql", page_size=1)

    assert page.source == "tjba_graphql"
    assert page.total >= 1
    assert len(page.results) == 1
    result = page.results[0]
    assert result.source_trace is not None
    document_url = urlparse(result.raw["document_url"])
    assert document_url.scheme == "https"
    assert document_url.netloc == "jurisprudenciaws.tjba.jus.br"
    assert document_url.path.startswith("/inteiroTeor/")

    document = client.get_document(result.id, source="tjba_graphql")

    assert document.access_status.value == "public"
    assert document.extraction_status.value == "complete"
    assert document.text
    assert document.sha256
    assert document.source_trace is not None


@pytest.mark.live
def test_live_tjba_second_page_is_reproducible():
    """Keep the GraphQL zero-based page contract covered against the source."""

    client = NanoJurisClient(config=NanoJurisConfig(timeout=45, rate_limit_interval=0.5))
    page = client.search("dano moral", source="tjba_graphql", page=2, page_size=1)

    assert page.source == "tjba_graphql"
    assert page.page == 2
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.total > 0
    assert page.results


@pytest.mark.live
def test_live_tjba_explicit_nonexistent_process_is_empty():
    """A deterministic impossible CNJ number must remain a real empty page."""

    client = NanoJurisClient(config=NanoJurisConfig(timeout=45, rate_limit_interval=0.5))
    page = client.search(
        "",
        source="tjba_graphql",
        number="0000000-00.0000.0.00.0000",
        page_size=1,
    )

    assert page.source == "tjba_graphql"
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.total == 0
    assert page.results == []
    assert page.is_complete is True
