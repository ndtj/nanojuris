from __future__ import annotations

import json
from pathlib import Path

from nanojuris.cli import main
from nanojuris.models import CanonicalDecision, CanonicalDocument, CanonicalPrecedent, SearchPage
from nanojuris.route_probe import RouteProbeResult
from nanojuris.store import SQLiteStore


def _seed_store(path: Path) -> None:
    with SQLiteStore(path) as store:
        store.save_many(_records())


def _seed_run(path: Path) -> str:
    with SQLiteStore(path) as store:
        run = store.save_research_run(
            source="tjsp_cjsg",
            text="homicidio qualificado",
            query={"text": "homicidio qualificado"},
            records=_records(),
            label="Carteira criminal",
        )
    return run.id


def _records():
    return [
        CanonicalDecision(
            id="dec-1",
            source="tjsp_cjsg",
            court="TJSP",
            case_number="0003938-14.2017.8.26.0323",
            decision_type="acordao",
            subject="Homicidio Qualificado",
            rapporteur="Relator Exemplo",
            publication_date="2026-07-30",
        ),
        CanonicalPrecedent(
            id="prec-1",
            source="bnp_pangea",
            court="STJ",
            precedent_type="RR",
        ),
    ]


def test_cli_store_stats_outputs_counts(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    exit_code = main(["store", "stats", str(db_path)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] == 2
    assert payload["by_kind"] == {"decision": 1, "precedent": 1}
    assert payload["by_source"] == {"bnp_pangea": 1, "tjsp_cjsg": 1}


def test_cli_documento_outputs_canonical_document(monkeypatch, capsys):
    class FakeClient:
        def get_document(self, document_id, *, source):
            return CanonicalDocument(
                id=document_id,
                source=source,
                document_type="acordao",
                text="Inteiro teor publico",
            )

    monkeypatch.setattr("nanojuris.cli.NanoJurisClient", FakeClient)

    exit_code = main(["documento", "doc-1", "--fonte", "fake"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "doc-1"
    assert payload["source"] == "fake"
    assert payload["text"] == "Inteiro teor publico"


def test_cli_documento_compact_omits_long_fields(monkeypatch, capsys):
    class FakeClient:
        def get_document(self, document_id, *, source):
            return CanonicalDocument(
                id=document_id,
                source=source,
                document_type="acordao",
                text="Texto publico longo",
                raw_metadata={
                    "case_number": "0003938-14.2017.8.26.0323",
                    "case_class": "Acao Penal",
                    "movements_text": "movimentacao longa",
                },
            )

    monkeypatch.setattr("nanojuris.cli.NanoJurisClient", FakeClient)

    exit_code = main(["documento", "doc-1", "--fonte", "fake", "--compacto"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "doc-1"
    assert "text" not in payload
    assert payload["raw_metadata"] == {
        "case_number": "0003938-14.2017.8.26.0323",
        "case_class": "Acao Penal",
    }
    assert payload["omitted_fields"] == ["text", "raw_metadata.movements_text"]


def test_cli_tribunais_filters_brazilian_courts(capsys):
    exit_code = main(["tribunais", "--uf", "SP", "--implementados"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [court["code"] for court in payload] == ["TJSP"]
    assert payload[0]["providers"] == [
        "tjsp_cjsg",
        "tjsp_eproc_jurisprudencia",
    ]


def test_cli_tribunais_filters_by_branch(capsys):
    exit_code = main(["tribunais", "--ramo", "federal"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    codes = {court["code"] for court in payload}
    assert {"TRF1", "TRF6", "TNU"}.issubset(codes)


def test_cli_tribunais_filters_by_source_system(capsys):
    exit_code = main(["tribunais", "--sistema", "esaj_cjsg"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [court["code"] for court in payload] == ["TJAC", "TJAL", "TJAM", "TJMS", "TJSP"]
    assert payload[0]["source_system"] == "esaj_cjsg"


def test_cli_probe_rota_outputs_route_diagnostic(monkeypatch, capsys):
    calls = []

    def fake_probe_route(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return RouteProbeResult(
            ok=True,
            route_status="live_valid",
            quality_grade="A",
            score=10,
            url=url,
            final_url=url,
            status_code=200,
        )

    monkeypatch.setattr("nanojuris.cli.probe_route", fake_probe_route)

    exit_code = main(
        [
            "probe-rota",
            "https://example.test/juris",
            "--metodo",
            "POST",
            "--expect",
            "IDPJ",
            "--data",
            "q=idpj",
        ]
    )

    assert exit_code == 0
    assert calls[0]["url"] == "https://example.test/juris"
    assert calls[0]["method"] == "POST"
    assert calls[0]["expected_texts"] == ["IDPJ"]
    assert calls[0]["data"] == {"q": "idpj"}
    payload = json.loads(capsys.readouterr().out)
    assert payload["route_status"] == "live_valid"
    assert payload["quality_grade"] == "A"


def test_cli_probe_rota_accepts_json_file(monkeypatch, capsys):
    calls = []

    def fake_probe_route(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return RouteProbeResult(
            ok=True,
            route_status="live_valid",
            quality_grade="A",
            score=11,
            url=url,
            final_url=url,
            status_code=200,
        )

    monkeypatch.setattr("nanojuris.cli.probe_route", fake_probe_route)
    monkeypatch.setattr("nanojuris.cli._read_text_file", lambda path: '{"e":"horas extras"}')

    exit_code = main(
        [
            "probe-rota",
            "https://example.test/api",
            "--metodo",
            "POST",
            "--json-file",
            "payload.json",
        ]
    )

    assert exit_code == 0
    assert calls[0]["json_payload"] == {"e": "horas extras"}
    payload = json.loads(capsys.readouterr().out)
    assert payload["score"] == 11


def test_cli_probe_rota_accepts_json_array(monkeypatch, capsys):
    calls = []

    def fake_probe_route(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return RouteProbeResult(
            ok=True,
            route_status="live_valid",
            quality_grade="A",
            score=8,
            url=url,
            final_url=url,
            status_code=200,
        )

    monkeypatch.setattr("nanojuris.cli.probe_route", fake_probe_route)

    exit_code = main(
        [
            "probe-rota",
            "https://example.test/api/classes",
            "--metodo",
            "POST",
            "--json",
            '["TSE"]',
        ]
    )

    assert exit_code == 0
    assert calls[0]["json_payload"] == ["TSE"]
    payload = json.loads(capsys.readouterr().out)
    assert payload["quality_grade"] == "A"


def test_cli_contratos_outputs_source_contracts(capsys):
    exit_code = main(["contratos", "--fonte", "tjdf_juris"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["total_sources"] == 1
    assert payload["contracts"][0]["source"] == "tjdf_juris"
    assert payload["contracts"][0]["contract_level"] == 5


def test_cli_contratos_resumo_outputs_maturity_summary(capsys):
    exit_code = main(["contratos", "--resumo"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total_sources"] >= 1
    assert "needs_deepening" in payload
    assert "ready_for_agents" in payload


def test_cli_buscar_passes_number_filter(monkeypatch, capsys):
    calls = []

    class FakeClient:
        def search(self, text, **kwargs):
            calls.append({"text": text, **kwargs})
            return SearchPage(
                source="tjdf_juris",
                total=0,
                start=0,
                end=0,
                page=1,
                page_size=5,
                results=[],
            )

    monkeypatch.setattr("nanojuris.cli.NanoJurisClient", FakeClient)

    exit_code = main(
        [
            "buscar",
            "",
            "--fonte",
            "tjdf_juris",
            "--numero",
            "1500780-26.2025.8.26.0603",
            "--limite",
            "5",
        ]
    )

    assert exit_code == 0
    assert calls[0]["number"] == "1500780-26.2025.8.26.0603"
    assert calls[0]["source"] == "tjdf_juris"
    payload = json.loads(capsys.readouterr().out)
    assert payload["source"] == "tjdf_juris"


def test_cli_store_query_filters_records(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    exit_code = main(
        [
            "store",
            "query",
            str(db_path),
            "--kind",
            "decision",
            "--tribunal",
            "TJSP",
            "--assunto",
            "Homicidio Qualificado",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [record["id"] for record in payload] == ["dec-1"]
    assert payload[0]["case_number"] == "0003938-14.2017.8.26.0323"


def test_cli_store_query_compact_omits_long_fields(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    with SQLiteStore(db_path) as store:
        store.save(
            CanonicalDocument(
                id="doc-1",
                source="tjsp_cjsg",
                document_type="acordao",
                text="texto longo publico",
                raw_metadata={"case_number": "0003938-14.2017.8.26.0323"},
            )
        )

    exit_code = main(["store", "query", str(db_path), "--kind", "document", "--compacto"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["id"] == "doc-1"
    assert "text" not in payload[0]
    assert payload[0]["omitted_fields"] == ["text"]


def test_cli_store_query_filters_by_canonical_key(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    exit_code = main(
        [
            "store",
            "query",
            str(db_path),
            "--canonical-key",
            "decision|tjsp_cjsg|tjsp|0003938-14.2017.8.26.0323|acordao",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [record["id"] for record in payload] == ["dec-1"]


def test_cli_store_get_returns_record(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    exit_code = main(["store", "get", str(db_path), "precedent", "prec-1"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "prec-1"
    assert payload["precedent_type"] == "RR"


def test_cli_store_get_returns_error_for_missing_record(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    exit_code = main(["store", "get", str(db_path), "decision", "missing"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Registro nao encontrado" in captured.err


def test_cli_store_runs_lists_saved_research_runs(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    run_id = _seed_run(db_path)

    exit_code = main(["store", "runs", str(db_path)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [run["id"] for run in payload] == [run_id]
    assert payload[0]["label"] == "Carteira criminal"


def test_cli_store_run_returns_saved_research_run(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    run_id = _seed_run(db_path)

    exit_code = main(["store", "run", str(db_path), run_id])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == run_id
    assert payload["query"] == {"text": "homicidio qualificado"}


def test_cli_store_records_returns_saved_research_run_records(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    run_id = _seed_run(db_path)

    exit_code = main(["store", "records", str(db_path), run_id])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [record["id"] for record in payload] == ["dec-1", "prec-1"]


def test_cli_store_records_accepts_offset(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    run_id = _seed_run(db_path)

    exit_code = main(["store", "records", str(db_path), run_id, "--limite", "1", "--offset", "1"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [record["id"] for record in payload] == ["prec-1"]


def test_cli_store_export_outputs_saved_run_csv(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    run_id = _seed_run(db_path)

    exit_code = main(["store", "export", str(db_path), run_id, "--formato", "csv"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "record_kind,id,source" in output
    assert "decision,dec-1,tjsp_cjsg" in output
    assert "precedent,prec-1,bnp_pangea" in output


def test_cli_store_export_accepts_offset(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    run_id = _seed_run(db_path)

    exit_code = main(
        ["store", "export", str(db_path), run_id, "--formato", "jsonl", "--offset", "1"]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert '"id": "prec-1"' in output
    assert '"id": "dec-1"' not in output


def test_cli_store_export_rejects_missing_run(tmp_path, capsys):
    db_path = tmp_path / "nanojuris.db"
    _seed_store(db_path)

    exit_code = main(["store", "export", str(db_path), "missing", "--formato", "markdown"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Busca salva nao encontrada" in captured.err
