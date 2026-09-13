"""Bounded live contract checks for the public TJPI/JusPI provider."""

from __future__ import annotations

import os

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjpi_juspi import TjpiJuspiProvider

pytestmark = pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_TJ_STATE_LIVE") != "1",
    reason="Set NANOJURIS_RUN_TJ_STATE_LIVE=1 to query the bounded TJPI source",
)


def test_live_tjpi_pages_have_public_text_and_distinct_windows() -> None:
    provider = TjpiJuspiProvider(NanoJurisConfig(timeout=30, rate_limit_interval=0))
    first = provider.search(JurisprudenceQuery(text="dano moral", page=1, page_size=3))
    second = provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=3))

    assert first.source_trace is not None and first.source_trace.http_status == 200
    assert second.source_trace is not None and second.source_trace.http_status == 200
    assert first.total_known is True and second.total_known is True
    assert first.results and second.results
    assert {item.id for item in first.results}.isdisjoint({item.id for item in second.results})
    assert second.start > first.end
    assert all(item.summary or item.full_text for item in first.results + second.results)


def test_live_tjpi_process_number_and_explicit_empty_are_distinct() -> None:
    provider = TjpiJuspiProvider(NanoJurisConfig(timeout=30, rate_limit_interval=0))
    seed = provider.search(JurisprudenceQuery(text="dano moral", page=1, page_size=1))
    assert seed.results
    number = seed.results[0].number
    assert number

    by_number = provider.search(JurisprudenceQuery(number=number, page_size=3))
    assert by_number.source_trace is not None and by_number.source_trace.http_status == 200
    # The public index can rotate between the seed and the follow-up request.
    # An authoritative empty response is valid; only a blocked/error response
    # must remain distinct from an empty result.
    if not by_number.results:
        assert by_number.is_explicit_empty
        assert by_number.completeness_reason
    if by_number.results:
        assert any(result.number == number for result in by_number.results)

    empty = provider.search(JurisprudenceQuery(text="9999999-99.9999.9.99.9999", page_size=3))
    assert empty.source_trace is not None and empty.source_trace.http_status == 200
    assert empty.results == []
    # JusPI explicitly renders its no-result marker, so this is a confirmed
    # empty page rather than an inconclusive extraction.
    assert empty.is_explicit_empty is True
    assert empty.extraction_status.value == "empty"
