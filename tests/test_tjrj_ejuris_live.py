"""Bounded public TJRJ eJURIS contract check (opt-in)."""

from __future__ import annotations

import os

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjrj_ejuris import TjrjEjurisProvider

pytestmark = pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_TJRJ_EJURIS_LIVE") != "1",
    reason="Set NANOJURIS_RUN_TJRJ_EJURIS_LIVE=1 to query the public TJRJ eJURIS endpoint",
)


def test_live_tjrj_ejuris_returns_bounded_second_degree_text() -> None:
    provider = TjrjEjurisProvider(NanoJurisConfig(timeout=30, rate_limit_interval=0.25))
    page = provider.search(
        JurisprudenceQuery(
            text="responsabilidade civil",
            degree="second",
            instance="second",
            branch="state",
            authority="TJRJ",
            collection="CJSG",
            source_origin="segundo grau",
            page_size=1,
        )
    )

    assert page.source == "tjrj_ejuris"
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.total_known is True
    assert page.results
    assert all(item.degree == "second" for item in page.results)
    assert all(item.full_text for item in page.results)
