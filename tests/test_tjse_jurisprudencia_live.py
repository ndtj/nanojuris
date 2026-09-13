from __future__ import annotations

import os

import pytest

from nanojuris.errors import AccessControlRequiredError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjse_jurisprudencia import TjseJurisprudenciaProvider


@pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_TJSE_LIVE") != "1",
    reason="set NANOJURIS_RUN_TJSE_LIVE=1 to run the bounded public TJSE check",
)
def test_tjse_live_form_reports_turnstile_without_false_empty() -> None:
    provider = TjseJurisprudenciaProvider()
    with pytest.raises(AccessControlRequiredError):
        provider.search(
            JurisprudenceQuery(
                text="responsabilidade civil",
                degree="second",
                instance="second",
                branch="state",
                authority="TJSE",
                page_size=1,
            )
        )
