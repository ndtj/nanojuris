from __future__ import annotations

import os

import pytest

from nanojuris import NanoJurisClient, NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError

pytestmark = pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_LIVE") != "1",
    reason="Set NANOJURIS_RUN_LIVE=1 to query live public sources",
)


@pytest.mark.live
def test_live_stj_informativo_uses_shared_html_parser():
    client = NanoJurisClient(config=NanoJurisConfig(timeout=30, rate_limit_interval=0.5))
    page = client.search("infanticidio", source="stj_informativo", page_size=1)

    assert page.source == "stj_informativo"
    assert page.source_trace is not None
    assert page.results
    assert page.results[0].raw["document_url"]


@pytest.mark.live
def test_live_stj_scon_uses_shared_html_parser_or_reports_access_state():
    client = NanoJurisClient(config=NanoJurisConfig(timeout=30, rate_limit_interval=0.5))
    try:
        page = client.search("responsabilidade civil", source="stj_scon", page_size=1)
    except AccessControlRequiredError as exc:
        assert "access" in str(exc).lower() or "scon" in str(exc).lower()
        return

    assert page.source == "stj_scon"
    assert page.source_trace is not None
    assert page.results
