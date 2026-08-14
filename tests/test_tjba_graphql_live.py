from __future__ import annotations

import os

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
    assert result.raw["document_url"].startswith("/inteiroTeor/")

    document = client.get_document(result.id, source="tjba_graphql")

    assert document.access_status.value == "public"
    assert document.extraction_status.value == "complete"
    assert document.text
    assert document.sha256
    assert document.source_trace is not None
