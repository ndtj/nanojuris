"""Bounded live checks for the already-implemented TJRO/TJGO adapters."""

from __future__ import annotations

import os

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjgo_projudi_jurisprudencia import (
    TjgoProjudiJurisprudenciaProvider,
)
from nanojuris.providers.tjro_jurisprudencia import TjroJurisprudenciaProvider

pytestmark = pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_TJ_STATE_LIVE") != "1",
    reason="Set NANOJURIS_RUN_TJ_STATE_LIVE=1 to query bounded TJRO/TJGO sources",
)


@pytest.mark.parametrize(
    ("source", "provider_factory"),
    [
        ("tjro_jurisprudencia", TjroJurisprudenciaProvider),
        ("tjgo_projudi_jurisprudencia", TjgoProjudiJurisprudenciaProvider),
    ],
)
def test_live_state_provider_returns_trace_and_text(source, provider_factory) -> None:
    provider = provider_factory(NanoJurisConfig(timeout=30, rate_limit_interval=0))
    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=1))

    assert page.source == source
    assert page.results
    assert page.total_known is True
    assert page.is_complete is False
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.source_trace.content_sha256
    assert page.source_trace.response_bytes and page.source_trace.response_bytes > 0
    assert any(result.summary or result.full_text for result in page.results)


def test_live_tjro_cjsg_degree_filter_returns_only_appellate_rows() -> None:
    provider = TjroJurisprudenciaProvider(NanoJurisConfig(timeout=35, rate_limit_interval=0))
    page = provider.search(
        JurisprudenceQuery(text="responsabilidade", collection="CJSG", page_size=3)
    )

    assert page.source_trace is not None and page.source_trace.http_status == 200
    assert page.results
    assert all(result.degree == "second" for result in page.results)
    assert all(result.instance == "second" for result in page.results)
    assert page.source_trace.query["filters"]["grau_jurisdicao"] == [2]


def test_live_tjgo_pages_are_reproducible_and_non_overlapping() -> None:
    """The public UI uses a fixed screen id plus a zero-based page position."""

    provider = TjgoProjudiJurisprudenciaProvider(NanoJurisConfig(timeout=35, rate_limit_interval=0))
    first = provider.search(JurisprudenceQuery(text="dano moral", page=1, page_size=3))
    second = provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=3))

    assert first.source_trace is not None and first.source_trace.http_status == 200
    assert second.source_trace is not None and second.source_trace.http_status == 200
    assert first.total_known is True and second.total_known is True
    assert first.results and second.results
    assert {item.id for item in first.results}.isdisjoint({item.id for item in second.results})
    assert second.start == first.end + 1


def test_live_tjgo_process_number_filter_and_empty_query() -> None:
    provider = TjgoProjudiJurisprudenciaProvider(NanoJurisConfig(timeout=35, rate_limit_interval=0))
    seed = provider.search(JurisprudenceQuery(text="dano moral", page=1, page_size=1))
    assert seed.results
    number = seed.results[0].number
    by_number = provider.search(JurisprudenceQuery(number=number, page=1, page_size=3))
    assert by_number.source_trace is not None
    assert by_number.source_trace.http_status == 200
    assert by_number.total_known is True
    assert by_number.results
    assert by_number.results[0].number == number

    empty = provider.search(
        JurisprudenceQuery(number="0000000-00.0000.0.00.0000", page=1, page_size=3)
    )
    assert empty.source_trace is not None
    assert empty.source_trace.http_status == 200
    assert empty.results == []
    assert empty.total_known is False
