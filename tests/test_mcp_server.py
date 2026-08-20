from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from nanojuris import mcp_server


class FakeFastMCP:
    instances = []

    def __init__(self, name: str):
        self.name = name
        self.tools = {}
        self.ran = False
        FakeFastMCP.instances.append(self)

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator

    def run(self):
        self.ran = True


def _install_fake_fastmcp(monkeypatch):
    FakeFastMCP.instances.clear()
    fake_module = SimpleNamespace(FastMCP=FakeFastMCP)
    monkeypatch.setattr(mcp_server, "import_module", lambda name: fake_module)
    return fake_module


def test_create_server_registers_expected_tools(monkeypatch):
    _install_fake_fastmcp(monkeypatch)

    server = mcp_server.create_server()

    assert server.name == "nanojuris"
    assert set(server.tools) == {
        "describe_source_dataset",
        "collect_jurisprudence",
        "discover_provider",
        "export_results",
        "get_decisions",
        "get_document",
        "list_courts",
        "list_source_datasets",
        "list_sources",
        "plan_source_sync",
        "sync_source_resource",
        "search_jurisprudence",
        "search_unified",
        "search_unified_store",
        "source_contracts",
        "source_diagnostics",
        "source_health",
        "source_validation",
        "store_export_run",
        "store_get",
        "store_query",
        "store_run",
        "store_run_records",
        "store_runs",
        "store_stats",
        "store_sync_manifests",
    }


def test_create_server_supports_mcp_v2_server_surface(monkeypatch):
    FakeFastMCP.instances.clear()

    def import_mcp_module(name):
        if name == "mcp.server.fastmcp":
            raise ModuleNotFoundError(name=name)
        return SimpleNamespace(MCPServer=FakeFastMCP)

    monkeypatch.setattr(mcp_server, "import_module", import_mcp_module)

    server = mcp_server.create_server()

    assert server.name == "nanojuris"
    assert "search_unified" in server.tools


def test_create_server_tools_delegate_to_tool_layer(monkeypatch):
    _install_fake_fastmcp(monkeypatch)
    calls = []

    def recorder(name):
        def inner(*args, **kwargs):
            calls.append((name, args, kwargs))
            return {"tool": name, "args": args, "kwargs": kwargs}

        return inner

    monkeypatch.setattr(
        mcp_server,
        "list_sources_tool",
        lambda: {"sources": [{"source": "fake"}]},
    )
    monkeypatch.setattr(
        mcp_server,
        "list_courts_tool",
        lambda **kwargs: {"courts": [kwargs]},
    )
    monkeypatch.setattr(
        mcp_server,
        "source_diagnostics_tool",
        lambda source: {"source": source},
    )
    monkeypatch.setattr(
        mcp_server,
        "source_contracts_tool",
        lambda source="": {"source": source, "contracts": []},
    )
    monkeypatch.setattr(
        mcp_server,
        "source_validation_tool",
        lambda **kwargs: {"sources": kwargs.get("sources"), "passed": True},
    )
    monkeypatch.setattr(mcp_server, "list_source_datasets_tool", recorder("datasets"))
    monkeypatch.setattr(mcp_server, "describe_source_dataset_tool", recorder("describe"))
    monkeypatch.setattr(mcp_server, "plan_source_sync_tool", recorder("plan_sync"))
    monkeypatch.setattr(mcp_server, "sync_source_resource_tool", recorder("sync"))

    def fake_search_tool(text, **kwargs):
        calls.append(("search", text, kwargs))
        return {"text": text, **kwargs}

    def fake_unified_tool(text, **kwargs):
        calls.append(("unified", text, kwargs))
        return {"text": text, **kwargs}

    def fake_unified_store_tool(text, **kwargs):
        calls.append(("unified_store", text, kwargs))
        return {"text": text, **kwargs}

    def fake_collect_tool(text, **kwargs):
        calls.append(("collect", text, kwargs))
        return {"text": text, **kwargs}

    monkeypatch.setattr(mcp_server, "search_jurisprudence_tool", fake_search_tool)
    monkeypatch.setattr(mcp_server, "search_unified_tool", fake_unified_tool)
    monkeypatch.setattr(mcp_server, "search_unified_store_tool", fake_unified_store_tool)
    monkeypatch.setattr(mcp_server, "collect_jurisprudence_tool", fake_collect_tool)

    server = mcp_server.create_server()

    assert server.tools["list_sources"]() == {"sources": [{"source": "fake"}]}
    assert server.tools["list_courts"](branch="state", state="SP") == {
        "courts": [{"branch": "state", "state": "SP", "source_system": None, "implemented": None}]
    }
    assert server.tools["source_diagnostics"]("tjsp_cjsg") == {"source": "tjsp_cjsg"}
    assert server.tools["source_contracts"]("tjdf_juris") == {
        "source": "tjdf_juris",
        "contracts": [],
    }
    assert server.tools["list_source_datasets"]()["tool"] == "datasets"
    assert server.tools["describe_source_dataset"]("dataset-1")["tool"] == "describe"
    assert server.tools["plan_source_sync"]("dataset-1")["tool"] == "plan_sync"
    assert server.tools["sync_source_resource"]("dataset-1", "resource-1")["tool"] == "sync"
    assert server.tools["source_validation"](["tjdf_juris"], text="icms")["passed"] is True
    assert (
        server.tools["search_jurisprudence"](
            "icms",
            source="tjsp_cjsg",
            source_origin="2g",
            page_size=3,
        )["source_origin"]
        == "2g"
    )
    assert server.tools["search_unified"]("icms", sources=["a", "b"])["sources"] == [
        "a",
        "b",
    ]
    assert server.tools["search_unified_store"]("icms", store_id="research")["text"] == "icms"
    assert server.tools["collect_jurisprudence"](
        "icms", source="fake", store_id="research"
    )["text"] == "icms"
    assert [call[0] for call in calls] == [
        "datasets",
        "describe",
        "plan_sync",
        "sync",
        "search",
        "unified",
        "unified_store",
        "collect",
    ]


def test_create_server_data_tools_delegate_to_tool_layer(monkeypatch):
    _install_fake_fastmcp(monkeypatch)
    monkeypatch.setenv("NANOJURIS_STORE_ROOT", ".nanojuris-test-stores")
    calls = []

    def recorder(name):
        def inner(*args, **kwargs):
            calls.append((name, args, kwargs))
            return {"tool": name, "args": args, "kwargs": kwargs}

        return inner

    monkeypatch.setattr(mcp_server, "export_results_tool", recorder("export"))
    monkeypatch.setattr(mcp_server, "get_document_tool", recorder("document"))
    monkeypatch.setattr(mcp_server, "get_decisions_tool", recorder("decisions"))
    monkeypatch.setattr(mcp_server, "store_stats_tool", recorder("stats"))
    monkeypatch.setattr(mcp_server, "store_sync_manifests_tool", recorder("manifests"))
    monkeypatch.setattr(mcp_server, "store_query_tool", recorder("query"))
    monkeypatch.setattr(mcp_server, "store_get_tool", recorder("get"))
    monkeypatch.setattr(mcp_server, "store_runs_tool", recorder("runs"))
    monkeypatch.setattr(mcp_server, "store_run_tool", recorder("run"))
    monkeypatch.setattr(mcp_server, "store_run_records_tool", recorder("run_records"))
    monkeypatch.setattr(mcp_server, "store_export_run_tool", recorder("export_run"))

    server = mcp_server.create_server()

    assert server.tools["export_results"]("icms", source="stj_scon")["tool"] == "export"
    assert server.tools["get_document"]("doc-1", source="tjsp_cjsg")["tool"] == "document"
    assert server.tools["get_decisions"]("prec-1", source="bnp_pangea")["tool"] == "decisions"
    assert server.tools["store_stats"]("nanojuris.db")["tool"] == "stats"
    assert (
        server.tools["store_sync_manifests"](
            "nanojuris.db", source="stj_dados_abertos_jurisprudencia"
        )["tool"]
        == "manifests"
    )
    assert server.tools["store_query"]("nanojuris.db", kind="decision")["tool"] == "query"
    assert server.tools["store_get"]("nanojuris.db", "decision", "dec-1")["tool"] == "get"
    assert server.tools["store_runs"]("nanojuris.db", limit=3)["tool"] == "runs"
    assert server.tools["store_run"]("nanojuris.db", "run-1")["tool"] == "run"
    assert (
        server.tools["store_run_records"]("nanojuris.db", "run-1", limit=2)["tool"] == "run_records"
    )
    assert (
        server.tools["store_export_run"]("nanojuris.db", "run-1", output_format="jsonl")["tool"]
        == "export_run"
    )
    assert [call[0] for call in calls] == [
        "export",
        "document",
        "decisions",
        "stats",
        "manifests",
        "query",
        "get",
        "runs",
        "run",
        "run_records",
        "export_run",
    ]


def test_create_server_rejects_invalid_enum_like_arguments(monkeypatch):
    _install_fake_fastmcp(monkeypatch)
    server = mcp_server.create_server()

    with pytest.raises(ValueError, match="branch"):
        server.tools["list_courts"](branch="unknown")

    with pytest.raises(ValueError, match="kind"):
        server.tools["store_query"]("nanojuris.db", kind="bad")

    with pytest.raises(ValueError, match="kind"):
        server.tools["store_get"]("nanojuris.db", "bad", "1")


def test_resolve_store_id_rejects_paths_and_stays_inside_root(monkeypatch):
    root = Path.cwd() / ".tmp" / "mcp-security-store"
    monkeypatch.setenv("NANOJURIS_STORE_ROOT", str(root))

    resolved = mcp_server._resolve_store_id("research")

    assert resolved == root.resolve() / "research.db"
    with pytest.raises(ValueError, match="filesystem path"):
        mcp_server._resolve_store_id("../outside")


def test_create_server_missing_optional_dependency(monkeypatch):
    def raise_import_error(name: str):
        raise ImportError(name)

    monkeypatch.setattr(mcp_server, "import_module", raise_import_error)

    with pytest.raises(RuntimeError, match="nanojuris\\[mcp\\]"):
        mcp_server.create_server()


def test_main_runs_created_server(monkeypatch):
    _install_fake_fastmcp(monkeypatch)

    mcp_server.main()

    assert FakeFastMCP.instances[-1].ran is True
