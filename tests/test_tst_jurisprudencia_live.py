"""Opt-in bounded live smoke for TST jurisprudence."""

from __future__ import annotations

import os

import pytest

from nanojuris import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tst_jurisprudencia import TstJurisprudenciaProvider


@pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_TST_LIVE") != "1",
    reason="Set NANOJURIS_RUN_TST_LIVE=1 to query the public TST source",
)
def test_tst_public_search_and_detail_live() -> None:
    provider = TstJurisprudenciaProvider(NanoJurisConfig(timeout=30, rate_limit_interval=0))
    page = provider.search(JurisprudenceQuery(text="responsabilidade civil", page_size=1))
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.results
    assert page.results[0].summary
    document = provider.get_document(page.results[0].id)
    assert document.text
    assert document.sha256
