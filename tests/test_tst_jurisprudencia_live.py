from __future__ import annotations

import os

import pytest

from nanojuris import NanoJurisClient, NanoJurisConfig

pytestmark = pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_LIVE") != "1",
    reason="Set NANOJURIS_RUN_LIVE=1 to query live public sources",
)


@pytest.mark.live
def test_live_tst_search_and_document_use_current_public_api():
    client = NanoJurisClient(config=NanoJurisConfig(timeout=30, rate_limit_interval=0))
    page = client.search("responsabilidade civil", source="tst_jurisprudencia", page_size=1)

    assert page.source == "tst_jurisprudencia"
    assert page.total > 0
    assert page.results
    assert (
        page.results[0]
        .raw["document_url"]
        .startswith("https://jurisprudencia-backend.tst.jus.br/rest/documentos/")
    )
    assert page.results[0].judgment_date or page.results[0].publication_date

    document = client.get_document(page.results[0].raw["document_url"], source="tst_jurisprudencia")
    assert document.access_status.value == "public"
    assert document.raw_bytes
    assert document.text
