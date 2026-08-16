from __future__ import annotations

import inspect

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.mcp_tools import (
    export_results_tool,
    get_decisions_tool,
    get_document_tool,
    list_courts_tool,
    list_sources_tool,
    search_jurisprudence_tool,
    search_unified_tool,
    source_contracts_tool,
    source_diagnostics_tool,
    store_export_run_tool,
    store_get_tool,
    store_query_tool,
    store_run_records_tool,
    store_run_tool,
    store_runs_tool,
    store_stats_tool,
)
from nanojuris.models import (
    CanonicalDecision,
    CanonicalDocument,
    CanonicalPrecedent,
    DecisionBundle,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.store import SQLiteStore


class FakeProvider:
    name = "fake"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        return SearchPage(
            source="fake",
            total=1,
            start=1,
            end=1,
            page=query.page,
            page_size=query.page_size,
            results=[
                JurisprudenceResult(
                    id="fake-1",
                    source="fake",
                    court="TJSP",
                    type="acordao",
                    number="0003938-14.2017.8.26.0323",
                    summary="Ementa publica",
                    source_trace=SourceTrace(provider="fake", endpoint="/search"),
                    raw={
                        "classe": "Apelacao Criminal",
                        "assunto": "Homicidio Qualificado",
                    },
                )
            ],
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(
            precedent_id=precedent_id,
            source="fake",
            texts=[{"content": "Decisao publica", "content_type": "text/plain"}],
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        return CanonicalDocument(
            id=document_id,
            source="fake",
            document_type="acordao",
            content_type="text/html",
            text="Inteiro teor publico",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source="fake",
            display_name="Fonte Fake",
            source_url="https://example.test",
            category="court_jurisprudence",
            search_modes=["text"],
            canonical_records=["CanonicalDecision"],
            supports_unified_search=True,
            supports_mcp=True,
        )


class RecordingProvider(FakeProvider):
    def __init__(self):
        self.query = None

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        self.query = query
        return super().search(query)


class FailingProvider:
    name = "failing"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        raise RuntimeError("fonte indisponivel")

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source="failing",
            display_name="Fonte Falha",
            source_url="https://example.test/failing",
            category="court_jurisprudence",
            search_modes=["text"],
            canonical_records=["CanonicalDecision"],
            supports_unified_search=True,
            supports_mcp=True,
        )


def _client() -> NanoJurisClient:
    return NanoJurisClient(providers=[FakeProvider()])


def _seed_store(path):
    with SQLiteStore(path) as store:
        store.save_many(
            [
                CanonicalDecision(
                    id="dec-1",
                    source="tjsp_cjsg",
                    court="TJSP",
                    case_number="0003938-14.2017.8.26.0323",
                    decision_type="acordao",
                    subject="Homicidio Qualificado",
                    publication_date="2026-07-30",
                ),
                CanonicalPrecedent(
                    id="prec-1",
                    source="bnp_pangea",
                    court="STJ",
                    precedent_type="RR",
                ),
            ]
        )


def _seed_run(path):
    with SQLiteStore(path) as store:
        run = store.save_research_run(
            source="tjsp_cjsg",
            text="homicidio qualificado",
            query={"text": "homicidio qualificado"},
            records=[
                CanonicalDecision(
                    id="dec-1",
                    source="tjsp_cjsg",
                    court="TJSP",
                    case_number="0003938-14.2017.8.26.0323",
                    decision_type="acordao",
                    subject="Homicidio Qualificado",
                    publication_date="2026-07-30",
                )
            ],
            label="Carteira criminal",
        )
    return run.id


def _seed_multi_run(path):
    with SQLiteStore(path) as store:
        run = store.save_research_run(
            source="tjsp_cjsg",
            text="homicidio qualificado",
            query={"text": "homicidio qualificado"},
            records=[
                CanonicalDecision(
                    id=f"dec-{index}",
                    source="tjsp_cjsg",
                    court="TJSP",
                    case_number=f"0000000-00.2026.8.26.{index:04d}",
                    decision_type="acordao",
                    publication_date=f"2026-08-0{index}",
                )
                for index in range(1, 4)
            ],
            label="Carteira criminal",
        )
    return run.id


def test_list_sources_tool_returns_capabilities():
    payload = list_sources_tool(_client())

    assert payload["sources"][0]["capabilities"]["source"] == "fake"
    assert payload["sources"][0]["capabilities"]["canonical_records"] == ["CanonicalDecision"]
    assert payload["sources"][0]["coverage"] is None


def test_list_courts_tool_filters_brazilian_courts():
    payload = list_courts_tool(branch="state", state="SP", implemented=True)

    assert [court["code"] for court in payload["courts"]] == ["TJSP"]
    assert payload["courts"][0]["providers"] == (
        "tjsp_cjsg",
        "tjsp_eproc_jurisprudencia",
    )


def test_list_courts_tool_filters_by_source_system():
    payload = list_courts_tool(source_system="esaj_cjsg")

    assert [court["code"] for court in payload["courts"]] == [
        "TJAC",
        "TJAL",
        "TJAM",
        "TJMS",
        "TJSP",
    ]
    assert payload["courts"][0]["source_system"] == "esaj_cjsg"


def test_source_diagnostics_tool_returns_one_source():
    payload = source_diagnostics_tool("fake", client=_client())

    assert payload["source"] == "fake"
    assert payload["capabilities"]["display_name"] == "Fonte Fake"


def test_source_contracts_tool_returns_contract_maturity():
    payload = source_contracts_tool(client=_client())

    assert payload["summary"]["total_sources"] == 1
    assert payload["contracts"][0]["source"] == "fake"
    assert payload["contracts"][0]["contract_level"] >= 1
    assert "next_steps" in payload["contracts"][0]


def test_source_contracts_tool_filters_one_source():
    payload = source_contracts_tool("fake", client=_client())

    assert payload["summary"]["total_sources"] == 1
    assert [contract["source"] for contract in payload["contracts"]] == ["fake"]


def test_search_jurisprudence_tool_returns_canonical_records_and_limits_page_size():
    payload = search_jurisprudence_tool(
        "homicidio",
        source="fake",
        page_size=500,
        client=_client(),
    )

    assert payload["canonical"] is True
    assert payload["page_size"] == 100
    assert payload["results"][0]["case_number"] == "0003938-14.2017.8.26.0323"
    assert payload["results"][0]["subject"] == "Homicidio Qualificado"


def test_search_jurisprudence_tool_normalizes_invalid_page():
    payload = search_jurisprudence_tool(
        "homicidio",
        source="fake",
        page=0,
        client=_client(),
    )

    assert payload["page"] == 1


def test_search_tools_expose_and_forward_refinement_filters():
    expected = {"date_from", "date_to", "exact_phrase", "rapporteur"}
    assert expected <= set(inspect.signature(search_jurisprudence_tool).parameters)
    assert expected <= set(inspect.signature(search_unified_tool).parameters)

    provider = RecordingProvider()
    search_jurisprudence_tool(
        "dano moral",
        source="fake",
        date_from="2021-01-01",
        date_to="2021-12-31",
        exact_phrase="transporte aereo",
        rapporteur="Relator Exemplo",
        client=NanoJurisClient(providers=[provider]),
    )

    assert provider.query is not None
    assert provider.query.published_from == "2021-01-01"
    assert provider.query.published_to == "2021-12-31"
    assert provider.query.exact_phrase == "transporte aereo"
    assert provider.query.rapporteur == "Relator Exemplo"


def test_search_jurisprudence_tool_can_return_normalized_page():
    payload = search_jurisprudence_tool(
        "homicidio",
        source="fake",
        canonical=False,
        client=_client(),
    )

    assert payload["source"] == "fake"
    assert payload["results"][0]["id"] == "fake-1"


def test_search_jurisprudence_tool_accepts_all_source_alias():
    payload = search_jurisprudence_tool(
        "homicidio",
        source="all",
        client=NanoJurisClient(providers=[FakeProvider(), FailingProvider()]),
    )

    assert payload["sources"] == ["failing", "fake"]
    assert payload["total_returned"] == 1
    assert payload["results"][0]["case_number"] == "0003938-14.2017.8.26.0323"
    assert payload["errors"][0]["source"] == "failing"


def test_search_unified_tool_returns_results_and_source_errors():
    payload = search_unified_tool(
        "homicidio",
        sources=["fake", "failing"],
        client=NanoJurisClient(providers=[FakeProvider(), FailingProvider()]),
    )

    assert payload["sources"] == ["fake", "failing"]
    assert payload["canonical"] is True
    assert payload["total_returned"] == 1
    assert payload["errors"] == [
        {
            "source": "failing",
            "error_type": "InternalProviderError",
            "message": "provider failing failed with an unexpected internal error",
        }
    ]


def test_export_results_tool_returns_requested_format():
    payload = export_results_tool(
        "homicidio",
        source="fake",
        output_format="canonical-jsonl",
        client=_client(),
    )

    assert payload["format"] == "canonical-jsonl"
    assert '"case_number": "0003938-14.2017.8.26.0323"' in payload["content"]


def test_export_results_tool_rejects_unknown_format():
    with pytest.raises(ValueError):
        export_results_tool("homicidio", source="fake", output_format="bad", client=_client())


def test_get_document_tool_returns_canonical_document():
    payload = get_document_tool("doc-1", source="fake", client=_client())

    assert payload["document_id"] == "doc-1"
    assert payload["document"]["document_type"] == "acordao"
    assert payload["document"]["text"] == "Inteiro teor publico"


def test_get_decisions_tool_returns_decision_bundle():
    payload = get_decisions_tool("prec-1", source="fake", client=_client())

    assert payload["precedent_id"] == "prec-1"
    assert payload["bundle"]["source"] == "fake"
    assert payload["bundle"]["texts"] == [
        {"content": "Decisao publica", "content_type": "text/plain"}
    ]


def test_store_stats_tool_returns_local_store_counts(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    payload = store_stats_tool(str(db_path))

    assert payload["total"] == 2
    assert payload["by_kind"] == {"decision": 1, "precedent": 1}
    assert payload["by_source"] == {"bnp_pangea": 1, "tjsp_cjsg": 1}


def test_store_query_tool_filters_and_limits_local_records(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    payload = store_query_tool(
        str(db_path),
        kind="decision",
        court="TJSP",
        subject="Homicidio Qualificado",
        limit=500,
    )

    assert payload["limit"] == 100
    assert payload["offset"] == 0
    assert payload["total"] == 1
    assert payload["has_more"] is False
    assert payload["next_offset"] is None
    assert [record["id"] for record in payload["results"]] == ["dec-1"]
    assert payload["results"][0]["case_number"] == "0003938-14.2017.8.26.0323"


def test_store_query_tool_filters_by_canonical_key(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    payload = store_query_tool(
        str(db_path),
        canonical_key="decision|tjsp_cjsg|tjsp|0003938-14.2017.8.26.0323|acordao",
    )

    assert [record["id"] for record in payload["results"]] == ["dec-1"]


def test_store_get_tool_returns_one_local_record(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    payload = store_get_tool(str(db_path), "precedent", "prec-1")

    assert payload["kind"] == "precedent"
    assert payload["record"]["precedent_type"] == "RR"


def test_store_get_tool_rejects_missing_record(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    payload = store_get_tool(str(db_path), "decision", "missing")

    assert payload == {
        "db_path": str(db_path),
        "kind": "decision",
        "id": "missing",
        "found": False,
        "record": None,
    }


def test_store_runs_tool_lists_saved_runs(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    run_id = _seed_run(db_path)

    payload = store_runs_tool(str(db_path))

    assert [run["id"] for run in payload["runs"]] == [run_id]
    assert payload["runs"][0]["label"] == "Carteira criminal"


def test_store_run_tool_returns_saved_run(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    run_id = _seed_run(db_path)

    payload = store_run_tool(str(db_path), run_id)

    assert payload["run"]["id"] == run_id
    assert payload["run"]["query"] == {"text": "homicidio qualificado"}


def test_store_run_tool_returns_not_found_without_exception(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    payload = store_run_tool(str(db_path), "missing")

    assert payload == {
        "db_path": str(db_path),
        "run_id": "missing",
        "found": False,
        "run": None,
    }


def test_store_run_records_tool_returns_saved_run_records(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    run_id = _seed_run(db_path)

    payload = store_run_records_tool(str(db_path), run_id)

    assert payload["run_id"] == run_id
    assert [record["id"] for record in payload["results"]] == ["dec-1"]


def test_store_run_records_tool_returns_pagination_metadata(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    run_id = _seed_multi_run(db_path)

    payload = store_run_records_tool(str(db_path), run_id, limit=2)

    assert payload["total"] == 3
    assert payload["offset"] == 0
    assert payload["has_more"] is True
    assert payload["next_offset"] == 2
    assert [record["id"] for record in payload["results"]] == ["dec-3", "dec-2"]


def test_store_export_run_tool_returns_saved_run_content(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    run_id = _seed_run(db_path)

    payload = store_export_run_tool(str(db_path), run_id, output_format="markdown")

    assert payload["run_id"] == run_id
    assert payload["format"] == "markdown"
    assert "# Pesquisa NanoJuris: Carteira criminal" in payload["content"]
    assert "0003938-14.2017.8.26.0323" in payload["content"]


def test_store_export_run_tool_accepts_offset(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    run_id = _seed_multi_run(db_path)

    payload = store_export_run_tool(str(db_path), run_id, output_format="jsonl", offset=2)

    assert payload["total"] == 3
    assert payload["has_more"] is False
    assert payload["next_offset"] is None
    assert '"id": "dec-1"' in payload["content"]
    assert '"id": "dec-2"' not in payload["content"]


def test_store_export_run_tool_rejects_missing_run(tmp_path):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    with pytest.raises(ValueError, match="Research run not found"):
        store_export_run_tool(str(db_path), "missing")
