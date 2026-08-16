from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris import NanoJurisClient

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "provider_contracts.json"


@pytest.fixture(scope="module")
def provider_contract_fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_provider_state_fixture_manifest_is_safe_and_complete(provider_contract_fixtures):
    client = NanoJurisClient()
    runtime_sources = {item.source for item in client.list_sources()}
    providers = provider_contract_fixtures["providers"]
    scenarios = provider_contract_fixtures["scenarios"]

    assert set(providers) <= runtime_sources
    assert {
        "cjf_jurisprudencia",
        "stf_juris",
        "stj_informativo",
        "stj_scon",
        "stm_jurisprudencia",
        "tce_sp_jurisprudencia",
        "tcu_jurisprudencia",
        "tjac_cjsg",
        "tjal_cjsg",
        "tjam_cjsg",
        "tjba_graphql",
        "tjgo_projudi_jurisprudencia",
        "tjms_cjsg",
        "tjpa_jurisprudencia_bff",
        "tjpb_pje_jurisprudencia",
        "tjpi_juspi",
        "tjrj_eproc_jurisprudencia",
        "tjrr_juris",
        "tjsp_cjsg",
        "tjsp_eproc_jurisprudencia",
        "trf5_jurisprudencia",
    } <= set(providers)
    assert set(scenarios) == {"success", "empty", "non_success"}

    serialized = FIXTURE_PATH.read_text(encoding="utf-8").lower()
    assert "cookie" not in serialized
    assert "authorization" not in serialized
    assert "private key" not in serialized

    for source, entry in providers.items():
        assert entry["scenarios"] == ["success", "empty", "non_success"]
        capability = client.get_capabilities(source=source)
        assert capability is not None
        allowed_access = {status.value for status in capability.access_statuses}
        for scenario in entry["scenarios"]:
            state = scenarios[scenario]
            assert state["access_status"] in allowed_access
            assert state["retrieval_status"]
            assert state["extraction_status"]


@pytest.mark.parametrize("scenario", ["success", "empty", "non_success"])
def test_provider_state_fixture_semantics_are_distinct(provider_contract_fixtures, scenario):
    state = provider_contract_fixtures["scenarios"][scenario]

    if scenario == "success":
        assert state["result_kind"] != "real_empty"
        assert state["retrieval_status"] == "ok"
    elif scenario == "empty":
        assert state["result_kind"] == "real_empty"
        assert state["retrieval_status"] == "ok"
    else:
        assert state["result_kind"] != "real_empty"
        assert state["access_status"] == "source_unavailable"
        assert state["retrieval_status"] == "unavailable"
