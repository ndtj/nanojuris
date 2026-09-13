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
    assert "TRESP" in codes
    assert "TJMMG" in codes


def test_get_court_normalizes_acronyms():
    court = get_court(" tj-sp ")

    assert court.code == "TJSP"
    assert court.state == "SP"
    assert court.official_url == "https://www.tjsp.jus.br/"
    assert court.source_system == "esaj_cjsg"
    assert court.provider_status == "implemented"
    assert court.providers == ("tjsp_cjsg", "tjsp_eproc_jurisprudencia")
    assert normalize_court_code(" trf-1 ") == "TRF1"


def test_list_courts_filters_by_branch_state_and_status():
    state_courts = list_courts(branch="state")
    sao_paulo_courts = list_courts(state="sp")
    esaj_cjsg_courts = list_courts(source_system="esaj_cjsg")
    implemented = list_courts(implemented=True)

    assert len(state_courts) == 27
    assert [court.code for court in sao_paulo_courts] == ["TJMSP", "TJSP", "TRESP"]
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
        "TRESP",
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
    tjrn = get_court("TJRN")
    assert tjrn.source_system == "portal_proprio"
    assert tjrn.providers == ("tjrn_jurisprudencia",)
    tjro = get_court("TJRO")
    assert tjro.source_system == "portal_proprio"
    assert tjro.providers == ("tjro_jurisprudencia", "tjro_liame")


def test_regional_electoral_and_state_military_catalog_entries_are_explicit():
    tres = list_courts(branch="electoral")
    tjms = list_courts(branch="military", state="sp")
    tre_codes = {court.code for court in tres if court.code.startswith("TRE")}
    expected_states = {
        "AC",
        "AL",
        "AP",
        "AM",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MT",
        "MS",
        "MG",
        "PA",
        "PB",
        "PR",
        "PE",
        "PI",
        "RJ",
        "RN",
        "RS",
        "RO",
        "RR",
        "SC",
        "SP",
        "SE",
        "TO",
    }

    assert len(tres) == 28  # TSE plus 27 TREs
    assert tre_codes == {f"TRE{state}" for state in expected_states}
    assert get_court("TRE-SP").code == "TRESP"
    assert get_court("TRE-SP").providers == ("tre_sp_temas",)
    assert [court.code for court in tjms] == ["TJMSP"]
    assert {court.code for court in list_courts(branch="military")} == {
        "STM",
        "TJMMG",
        "TJMSP",
        "TJMRS",
    }


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
