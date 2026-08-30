from __future__ import annotations

import os

import pytest

from nanojuris import NanoJurisClient

pytestmark = pytest.mark.skipif(
    os.getenv("NANOJURIS_RUN_LIVE") != "1",
    reason="Set NANOJURIS_RUN_LIVE=1 to query live public sources",
)


@pytest.mark.live
def test_live_bnp_catalog_has_core_courts_and_species():
    catalog = NanoJurisClient().get_catalog()

    court_codes = {court.code for court in catalog.courts}
    species_codes = {species.code for species in catalog.species}

    assert {"STF", "STJ", "TST"}.issubset(court_codes)
    assert {"RG", "RR", "IAC", "IRDR", "SUM", "SV"}.issubset(species_codes)
    assert catalog.source_trace is not None


@pytest.mark.live
def test_live_bnp_search_returns_trace_and_result():
    page = NanoJurisClient().search(
        "ICMS",
        courts=["STF", "STJ"],
        types=["RG", "RR"],
        page_size=1,
    )

    assert page.total >= 1
    assert len(page.results) == 1
    assert page.results[0].source_trace is not None
    assert page.source_trace is not None


@pytest.mark.live
def test_live_bnp_search_without_filters_defaults_to_full_catalog():
    # The /precedentes endpoint rejects empty 'orgaos'/'tipos'; the provider
    # must backfill them from the public catalog so a plain text search works.
    page = NanoJurisClient().search("responsabilidade civil", page_size=3)

    assert page.total >= 1
    assert page.results
    assert page.source_trace is not None
    sent = page.source_trace.query["filtro"]
    assert sent["orgaos"] and sent["tipos"]
