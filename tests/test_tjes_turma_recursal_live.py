"""Bounded live check for the official TJES Turma Recursal JSON route."""

from __future__ import annotations

import os

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjes_turma_recursal import TjesTurmaRecursalProvider


@pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_LIVE") != "1",
    reason="set NANOJURIS_RUN_LIVE=1 to enable bounded public-source checks",
)
def test_tjes_turma_recursal_live_public_json_contract() -> None:
    """Fetch one small public page without persisting the response body."""

    provider = TjesTurmaRecursalProvider(NanoJurisConfig(timeout=30, rate_limit_interval=0))
    page = provider.search(JurisprudenceQuery(text="dano moral", page=1, page_size=1))

    assert page.source == "tjes_turma_recursal"
    assert page.results
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.source_trace.content_sha256
    assert page.source_trace.response_bytes and page.source_trace.response_bytes > 0
    assert any(result.full_text for result in page.results)
    assert all(result.raw.get("core") == "turma_recursal_legado" for result in page.results)
