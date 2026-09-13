from __future__ import annotations

import os

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, SourceUnavailableError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjsp_cjpg import TjspCjpgProvider

pytestmark = pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_TJSP_CJPG_LIVE") != "1",
    reason="Set NANOJURIS_RUN_TJSP_CJPG_LIVE=1 to query the public TJSP/CJPG page",
)


@pytest.mark.live
def test_live_tjsp_cjpg_public_search_contract() -> None:
    provider = TjspCjpgProvider(NanoJurisConfig(timeout=30, rate_limit_interval=0))
    try:
        page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=1))
    except (AccessControlRequiredError, SourceUnavailableError) as exc:
        # Public court portals may transiently apply WAF/rate limiting.  Keep
        # that outcome explicit instead of turning it into a false empty or a
        # permanently failing CI job.
        pytest.skip(f"TJSP CJPG live outcome: {type(exc).__name__}: {exc}")
    assert page.source == "tjsp_cjpg"
    assert page.total > 0
    assert page.results
    assert page.results[0].number
    assert page.results[0].full_text
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.source_trace.content_sha256
