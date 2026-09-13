"""Bounded public TJRN checks for page semantics and source traces."""

from __future__ import annotations

import os

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjrn_jurisprudencia import TjrnJurisprudenciaProvider

pytestmark = pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_TJRN_LIVE") != "1",
    reason="Set NANOJURIS_RUN_TJRN_LIVE=1 to query the public TJRN page",
)


def test_live_tjrn_pages_are_bounded_and_non_overlapping() -> None:
    provider = TjrnJurisprudenciaProvider(NanoJurisConfig(timeout=30, rate_limit_interval=0))
    pages = [
        provider.search(JurisprudenceQuery(text="responsabilidade", page=page_no, page_size=2))
        for page_no in (1, 2)
    ]

    assert all(page.source == "tjrn_jurisprudencia" for page in pages)
    assert all(page.source_trace is not None for page in pages)
    assert all(page.source_trace.http_status == 200 for page in pages if page.source_trace)
    assert all(page.total_known is True for page in pages)
    assert all(page.is_complete is False for page in pages)
    assert pages[0].start == 1
    assert pages[1].start == 3
    assert not ({item.id for item in pages[0].results} & {item.id for item in pages[1].results})
