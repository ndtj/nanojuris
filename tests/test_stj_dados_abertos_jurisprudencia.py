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
        self.content = (
            payload
            if isinstance(payload, bytes)
            else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        )
        self.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(self.content)),
        }
        self.closed = False

    def json(self):
        return self._payload

    def iter_content(self, *, chunk_size: int):
        yield self.content

    def close(self):
        self.closed = True


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


def test_sync_json_deduplicates_by_id_and_persists_a_research_run(tmp_path):
    resource = json.dumps(
        [
            {
                "id": "record-1",
                "numeroProcesso": "0000001-11.2026.8.05.0001",
                "numeroRegistro": "REG-1",
                "descricaoClasse": "Apelacao Civel",
                "ministroRelator": "Ministro de Fixture",
                "nomeOrgaoJulgador": "Primeira Turma",
                "ementa": "Ementa de fixture",
                "decisao": "Decisao de fixture",
                "dataDecisao": "01/08/2026",
                "dataPublicacao": "2026-08-02T00:00:00Z",
            },
            {
                "id": "record-1",
                "numeroProcesso": "0000001-11.2026.8.05.0001",
                "dataPublicacao": "2026-08-02",
                "ementa": "Ementa de fixture atualizada",
            },
            {"ementa": "Registro sem id"},
        ],
        ensure_ascii=False,
    ).encode("utf-8")
    provider, session = _provider(
        _payload("stj_ckan_package_show.json"),
        resource,
    )

    from nanojuris.store import SQLiteStore

    with SQLiteStore(tmp_path / "stj.db") as store:
        result = provider.sync_resource(
            "espelhos-de-acordaos-primeira-turma",
            "resource-json-1",
            store=store,
            max_bytes=10_000,
            label="fixture sync",
        )
        stored = store.list_records(source=provider.name)
        run = store.get_research_run(result.run_id)

    assert result.records_seen == 3
    assert result.records_saved == 1
    assert result.duplicate_records == 1
    assert result.invalid_records == 1
    assert result.content_sha256
    assert stored[0]["case_number"] == "0000001-11.2026.8.05.0001"
    assert stored[0]["publication_date"] == "2026-08-02"
    assert stored[0]["raw"]["ementa"] == "Ementa de fixture atualizada"
    assert run is not None and run["record_count"] == 1
    assert session.calls[-1]["stream"] is True


def test_sync_skips_matching_source_hash_and_force_refreshes(tmp_path):
    resource = json.dumps([{"id": "record-1", "ementa": "Ementa incremental"}]).encode("utf-8")
    provider, session = _provider(
        _payload("stj_ckan_package_show.json"),
        resource,
        _payload("stj_ckan_package_show.json"),
        _payload("stj_ckan_package_show.json"),
        resource,
    )

    from nanojuris.store import SQLiteStore

    with SQLiteStore(tmp_path / "incremental.db") as store:
        first = provider.sync_resource(
            "espelhos-de-acordaos-primeira-turma",
            "resource-json-1",
            store=store,
        )
        skipped = provider.sync_resource(
            "espelhos-de-acordaos-primeira-turma",
            "resource-json-1",
            store=store,
        )
        refreshed = provider.sync_resource(
            "espelhos-de-acordaos-primeira-turma",
            "resource-json-1",
            store=store,
            force=True,
        )
        manifest = store.get_sync_manifest(
            source=provider.name,
            dataset_id="espelhos-de-acordaos-primeira-turma",
            resource_id="resource-json-1",
        )
        manifests = store.list_sync_manifests(source=provider.name)

    assert first.skipped is False
    assert skipped.skipped is True
    assert skipped.records_saved == 0
    assert skipped.run_id == first.run_id
    assert refreshed.skipped is False
    assert refreshed.run_id != first.run_id
    assert len(session.calls) == 5
    assert manifest is not None
    assert manifest["source_hash"] == "sha256:fixture-json"
    assert manifest["run_id"] == refreshed.run_id
    assert len(manifests) == 1


def test_sync_rejects_resource_that_exceeds_byte_limit(tmp_path):
    provider, _ = _provider(
        _payload("stj_ckan_package_show.json"),
        b'{"id": "too-large"}',
    )

    from nanojuris.store import SQLiteStore

    with SQLiteStore(tmp_path / "stj.db") as store:
        with pytest.raises(QueryRejectedError, match="excede max_bytes"):
            provider.sync_resource(
                "espelhos-de-acordaos-primeira-turma",
                "resource-json-1",
                store=store,
                max_bytes=1,
            )


def test_sync_rejects_zip_resources_before_download(tmp_path):
    package = _payload("stj_ckan_package_show.json")
    package["result"]["resources"].append(
        {
            "id": "resource-zip-1",
            "format": "ZIP",
            "url": "https://dadosabertos.web.stj.jus.br/resource/resource-zip-1",
        }
    )
    provider, session = _provider(package)

    from nanojuris.store import SQLiteStore

    with SQLiteStore(tmp_path / "zip.db") as store:
        with pytest.raises(UnsupportedQueryError, match="somente recursos JSON ou CSV"):
            provider.sync_resource(
                "espelhos-de-acordaos-primeira-turma",
                "resource-zip-1",
                store=store,
            )
    assert len(session.calls) == 1


def test_sync_rejects_resource_outside_official_domain(tmp_path):
    package = _payload("stj_ckan_package_show.json")
    package["result"]["resources"][0]["url"] = "https://example.com/resource.json"
    provider, session = _provider(package)

    from nanojuris.store import SQLiteStore

    with SQLiteStore(tmp_path / "domain.db") as store:
        with pytest.raises(QueryRejectedError, match="dominio oficial"):
            provider.sync_resource(
                "espelhos-de-acordaos-primeira-turma",
                "resource-json-1",
                store=store,
            )
    assert len(session.calls) == 1


def test_sync_rejects_invalid_json_resource(tmp_path):
    provider, _ = _provider(
        _payload("stj_ckan_package_show.json"),
        b"not-json",
    )

    from nanojuris.store import SQLiteStore

    with SQLiteStore(tmp_path / "invalid-json.db") as store:
        with pytest.raises(ParserContractChangedError, match="JSON resource is invalid"):
            provider.sync_resource(
                "espelhos-de-acordaos-primeira-turma",
                "resource-json-1",
                store=store,
            )


def test_trace_uses_supplied_bytes_after_stream_consumption():
    provider, _ = _provider()
    consumed = FakeResponse(
        b"payload",
        url="https://dadosabertos.web.stj.jus.br/resource/resource-json-1",
    )
    list(consumed.iter_content(chunk_size=64))
    trace = provider._trace(
        "GET resource/resource-json-1",
        query={},
        response=consumed,
        content=b"payload",
        limitations=[],
    )
    assert trace.response_bytes == len(b"payload")


def test_sync_csv_preserves_accents_and_unknown_fields(tmp_path):
    resource = (
        b"id;numeroProcesso;descricaoClasse;ementa;dataPublicacao;campoNovo\n"
        b"csv-1;0000002-22.2026.8.05.0001;Apelacao Civel;Ementa com acentuacao;"
        b"02/08/2026;valor preservado\n"
    )
    provider, _ = _provider(_payload("stj_ckan_package_show.json"), resource)

    from nanojuris.store import SQLiteStore

    with SQLiteStore(tmp_path / "stj-csv.db") as store:
        result = provider.sync_resource(
            "espelhos-de-acordaos-primeira-turma",
            "resource-csv-1",
            store=store,
        )
        stored = store.list_records(source=provider.name)

    assert result.format == "CSV"
    assert result.records_saved == 1
    assert stored[0]["case_number"] == "0000002-22.2026.8.05.0001"
    assert stored[0]["publication_date"] == "2026-08-02"
    assert stored[0]["raw"]["campoNovo"] == "valor preservado"


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


def test_client_and_mcp_sync_surface_persist_a_bounded_resource(tmp_path):
    from nanojuris.client import NanoJurisClient
    from nanojuris.mcp_tools import store_sync_manifests_tool, sync_source_resource_tool
    from nanojuris.store import SQLiteStore

    resource = json.dumps([{"id": "mcp-1", "ementa": "Registro MCP"}]).encode("utf-8")
    provider, _ = _provider(_payload("stj_ckan_package_show.json"), resource)
    client = NanoJurisClient(providers=[provider])

    with SQLiteStore(tmp_path / "client.db") as store:
        result = client.sync_source_resource(
            source=provider.name,
            dataset_id="espelhos-de-acordaos-primeira-turma",
            resource_id="resource-json-1",
            store=store,
        )
    assert result["records_saved"] == 1
    assert result["run_id"].startswith("run-")

    tool_provider, _ = _provider(_payload("stj_ckan_package_show.json"), resource)
    tool_client = NanoJurisClient(providers=[tool_provider])
    payload = sync_source_resource_tool(
        "espelhos-de-acordaos-primeira-turma",
        "resource-json-1",
        str(tmp_path / "mcp.db"),
        source=tool_provider.name,
        client=tool_client,
    )
    assert payload["sync"]["records_saved"] == 1
    manifests = store_sync_manifests_tool(str(tmp_path / "mcp.db"), source=tool_provider.name)
    assert manifests["manifests"][0]["resource_id"] == "resource-json-1"
