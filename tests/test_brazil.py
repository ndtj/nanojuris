from __future__ import annotations

import pytest

from nanojuris import COURTS, get_court, list_courts, normalize_court_code


def test_court_catalog_contains_brazilian_judiciary_core():
    codes = {court.code for court in COURTS}

    assert "STF" in codes
    assert "STJ" in codes
    assert "TJSP" in codes
    assert "TRF6" in codes
    assert "TRT24" in codes


def test_get_court_normalizes_acronyms():
    court = get_court(" tj-sp ")

    assert court.code == "TJSP"
    assert court.state == "SP"
    assert court.official_url == "https://www.tjsp.jus.br/"
    assert court.source_system == "esaj_cjsg"
    assert court.provider_status == "implemented"
    assert court.providers == ("tjsp_cjsg", "tjsp_eproc_jurisprudencia", "tjsp_esaj_cpopg")
    assert normalize_court_code(" trf-1 ") == "TRF1"


def test_list_courts_filters_by_branch_state_and_status():
    state_courts = list_courts(branch="state")
    sao_paulo_courts = list_courts(state="sp")
    esaj_cjsg_courts = list_courts(source_system="esaj_cjsg")
    implemented = list_courts(implemented=True)

    assert len(state_courts) == 27
    assert [court.code for court in sao_paulo_courts] == ["TJSP"]
    assert [court.code for court in esaj_cjsg_courts] == [
        "TJAC",
        "TJAL",
        "TJAM",
        "TJMS",
        "TJSP",
    ]
    assert [court.code for court in implemented] == [
        "STF",
        "STJ",
        "STM",
        "TJAC",
        "TJAL",
        "TJAM",
        "TJBA",
        "TJDFT",
        "TJGO",
        "TJMS",
        "TJPI",
        "TJRR",
        "TJSP",
        "TNU",
        "TRF2",
        "TRF4",
        "TRF6",
        "TST",
    ]
    assert get_court("TNU").providers == ("tnu_eproc_jurisprudencia",)
    assert get_court("TRF2").providers == ("trf2_eproc_jurisprudencia",)
    assert get_court("TRF6").providers == ("trf6_eproc_jurisprudencia",)
    tjpi = get_court("TJPI")
    assert tjpi.source_system == "portal_proprio"
    assert tjpi.providers == ("tjpi_juspi",)
    tjgo = get_court("TJGO")
    assert tjgo.source_system == "projudi_jurisprudencia"
    assert tjgo.providers == ("tjgo_projudi_jurisprudencia",)


def test_core_courts_include_official_urls_and_source_systems():
    stf = get_court("STF")
    stj = get_court("STJ")
    cnj = get_court("CNJ")

    assert stf.official_url == "https://portal.stf.jus.br/"
    assert stf.source_system == "portal_proprio"
    assert stf.provider_status == "implemented"
    assert stf.providers == ("stf_juris",)
    assert stj.official_url == "https://www.stj.jus.br/sites/portalp/Inicio"
    assert stj.source_system == "portal_proprio"
    assert stj.provider_status == "implemented"
    assert stj.providers == ("stj_scon", "stj_dados_abertos_jurisprudencia")
    assert cnj.official_url == "https://www.cnj.jus.br/sistemas/datajud/"
    assert cnj.source_system == "datajud"


def test_get_court_rejects_unknown_code():
    with pytest.raises(KeyError, match="Unknown Brazilian court code"):
        get_court("XYZ")
