from __future__ import annotations

import pytest

from nanojuris import NanoJurisClient

GOLD_SEARCH_CONTRACTS = {
    "tjdf_juris": ("page", "reported_total_and_page_window"),
    "tjgo_projudi_jurisprudencia": ("page", "reported_total_and_page_window"),
    "tjpi_juspi": ("page", "reported_total_and_page_window"),
    "tjpa_jurisprudencia_bff": ("page", "reported_total_and_page_window"),
    "tjpb_pje_jurisprudencia": ("page", "reported_total_and_page_window"),
    "tjrs_solr": ("offset", "reported_total_and_offset_window"),
    "tst_jurisprudencia": ("offset", "reported_total_and_offset_window"),
    "stm_jurisprudencia": ("offset", "reported_total_and_offset_window"),
    "stj_informativo": ("local_window", "observed_window_only"),
}


@pytest.mark.parametrize("source", sorted(GOLD_SEARCH_CONTRACTS))
def test_gold_provider_declares_explicit_pagination_contract(source: str) -> None:
    client = NanoJurisClient()
    capability = client.get_capabilities(source=source)

    assert capability is not None
    expected_mode, expected_completeness = GOLD_SEARCH_CONTRACTS[source]
    assert capability.pagination_mode == expected_mode
    assert capability.completeness_contract == expected_completeness
    assert capability.supports_unified_search is True
    assert capability.supports_live_tests is True
