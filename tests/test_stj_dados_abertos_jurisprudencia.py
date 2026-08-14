from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    ParserContractChangedError,
    QueryRejectedError,
    SourceUnavailableError,
    UnsupportedQueryError,
)
from nanojuris.providers.stj_dados_abertos_jurisprudencia import (
    StjDadosAbertosProvider,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, payload: object, *, url: str, status_code: int = 200):
        self._payload = payload
        self.url = url
        self.status_code = status_code
        self.content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.headers = {"Content-Type": "application/json"}

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses: list[FakeResponse]):
        self.responses = iter(responses)
        self.calls: list[dict[str, object]] = []
        self.trust_env = True
        self.verify = True

    def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return next(self.responses)


def _payload(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _provider(*payloads: object) -> tuple[StjDadosAbertosProvider, FakeSession]:
    session = FakeSession(
        [
            FakeResponse(payload, url="https://dadosabertos.web.stj.jus.br/api/3/action")
            for payload in payloads
        ]
    )
    return StjDadosAbertosProvider(NanoJurisConfig(rate_limit_interval=0), session), session


def test_list_datasets_returns_compact_catalog_metadata():
    provider, session = _provider(_payload("stj_ckan_package_search.json"))

    datasets = provider.list_source_datasets(rows=20)

    assert len(datasets) == 2
    assert datasets[0]["name"] == "espelhos-de-acordaos-primeira-turma"
    assert datasets[0]["formats"] == ["CSV", "JSON"]
    assert datasets[0]["resource_count"] == 2
    assert session.calls[0]["params"] == {"q": "jurisprudencia", "rows": 20}


def test_catalog_and_dataset_description_preserve_trace_and_resources():
    provider, session = _provider(
        _payload("stj_ckan_package_search.json"),
        _payload("stj_ckan_package_show.json"),
    )

    catalog = provider.get_catalog()
    description = provider.describe_dataset("espelhos-de-acordaos-primeira-turma")

    assert [item.code for item in catalog.courts] == ["STJ"]
    assert catalog.species[0].metadata["formats"] == ["CSV", "JSON"]
    assert catalog.source_trace is not None
    assert description["resources"][0]["hash"] == "sha256:fixture-json"
    assert description["source_trace"]["http_status"] == 200
    assert session.calls[1]["params"] == {"id": "espelhos-de-acordaos-primeira-turma"}


def test_sync_plan_is_bounded_and_never_downloads_resources():
    provider, session = _provider(_payload("stj_ckan_package_show.json"))

    plan = provider.plan_source_sync(
        "espelhos-de-acordaos-primeira-turma", format="json", max_resources=1
    )

    assert plan["download"] is False
    assert plan["format"] == "JSON"
    assert plan["resource_count"] == 1
    assert plan["resources"][0]["url"].endswith("resource-json-1")
    assert len(session.calls) == 1


def test_capabilities_explicitly_exclude_unified_search():
    provider, _ = _provider()

    capabilities = provider.get_capabilities()

    assert capabilities.supports_catalog is True
    assert capabilities.supports_unified_search is False
    assert capabilities.supports_mcp is True
    assert "dataset_id" in capabilities.supported_filters


def test_catalog_provider_rejects_remote_search_and_decision_detail():
    provider, _ = _provider()

    with pytest.raises(UnsupportedQueryError, match="nao oferece busca"):
        provider.search(None)  # type: ignore[arg-type]
    with pytest.raises(UnsupportedQueryError, match="nao possui detalhe"):
        provider.get_decisions("dataset-1")


@pytest.mark.parametrize("value", ["", "a\nb", "x" * 201])
def test_dataset_id_is_validated(value):
    provider, _ = _provider(_payload("stj_ckan_package_show.json"))

    with pytest.raises(QueryRejectedError):
        provider.describe_dataset(value)


def test_invalid_format_is_rejected_before_network_call():
    provider, session = _provider()

    with pytest.raises(QueryRejectedError, match="JSON, CSV ou ZIP"):
        provider.plan_source_sync("dataset-1", format="PDF")
    assert session.calls == []


@pytest.mark.parametrize("payload", [{"success": False}, {"success": True, "result": []}])
def test_invalid_ckan_envelope_is_not_silently_treated_as_empty(payload):
    provider, _ = _provider(payload)

    with pytest.raises(ParserContractChangedError):
        provider.list_source_datasets()


def test_http_error_is_classified():
    response = FakeResponse({}, url="https://dadosabertos.web.stj.jus.br", status_code=503)
    provider = StjDadosAbertosProvider(
        NanoJurisConfig(rate_limit_interval=0), FakeSession([response])
    )

    with pytest.raises(SourceUnavailableError, match="HTTP 503"):
        provider.list_source_datasets()


def test_client_and_mcp_catalog_surface_are_available():
    from nanojuris.client import NanoJurisClient
    from nanojuris.mcp_tools import list_source_datasets_tool, plan_source_sync_tool

    provider, _ = _provider(_payload("stj_ckan_package_search.json"))
    client = NanoJurisClient(providers=[provider])

    assert client.list_source_datasets(source=provider.name)[0]["name"].startswith("espelhos")
    tool_provider, _ = _provider(_payload("stj_ckan_package_search.json"))
    tool_client = NanoJurisClient(providers=[tool_provider])
    assert (
        list_source_datasets_tool(source=tool_provider.name, client=tool_client)["source"]
        == provider.name
    )

    plan_provider, _ = _provider(_payload("stj_ckan_package_show.json"))
    plan_client = NanoJurisClient(providers=[plan_provider])
    plan = plan_source_sync_tool(
        "espelhos-de-acordaos-primeira-turma", client=plan_client, max_resources=1
    )
    assert plan["download"] is False
