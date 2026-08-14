from __future__ import annotations

import sqlite3

from nanojuris.models import (
    CanonicalDecision,
    CanonicalDocument,
    CanonicalPrecedent,
    ExtractionTrace,
    ParadigmCase,
    SourceTrace,
)
from nanojuris.store import CanonicalStore, SQLiteStore


def _accepts_store(store: CanonicalStore) -> int:
    return store.count()


def test_sqlite_store_enables_foreign_keys_per_connection():
    store = SQLiteStore(":memory:")

    row = store.connection.execute("PRAGMA foreign_keys").fetchone()

    assert row is not None
    assert row[0] == 1


def test_sqlite_store_migrates_legacy_sync_manifest_schema():
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE research_runs (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            text TEXT NOT NULL,
            query_json TEXT NOT NULL,
            record_count INTEGER NOT NULL,
            label TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE source_sync_manifests (
            source TEXT NOT NULL,
            dataset_id TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            format TEXT NOT NULL,
            source_url TEXT,
            source_hash TEXT,
            content_sha256 TEXT NOT NULL,
            response_bytes INTEGER NOT NULL,
            records_seen INTEGER NOT NULL,
            records_saved INTEGER NOT NULL,
            duplicate_records INTEGER NOT NULL,
            invalid_records INTEGER NOT NULL,
            run_id TEXT NOT NULL,
            status TEXT NOT NULL,
            synced_at TEXT NOT NULL,
            PRIMARY KEY (source, dataset_id, resource_id)
        )
        """
    )

    SQLiteStore(connection)

    columns = {
        str(row[1])
        for row in connection.execute("PRAGMA table_info(source_sync_manifests)").fetchall()
    }
    assert "source_fingerprint" in columns


def test_sqlite_store_saves_and_gets_canonical_decision():
    store = SQLiteStore(":memory:")
    decision = CanonicalDecision(
        id="dec-1",
        source="tjsp_cjsg",
        court="TJSP",
        case_number="0003938-14.2017.8.26.0323",
        case_class="Apelacao Criminal",
        subject="Homicidio Qualificado",
        source_trace=SourceTrace(provider="tjsp_cjsg", endpoint="/resultadoCompleta.do"),
        extraction_trace=ExtractionTrace(parser="tjsp.parser", parser_version="1"),
    )

    store.save(decision)

    assert store.count() == 1
    assert store.count(kind="decision") == 1
    stored = store.get("decision", "dec-1")
    assert stored is not None
    assert stored["case_number"] == "0003938-14.2017.8.26.0323"
    assert stored["source_trace"]["provider"] == "tjsp_cjsg"
    assert stored["extraction_trace"]["parser"] == "tjsp.parser"
    assert _accepts_store(store) == 1


def test_sqlite_store_saves_many_and_filters_by_source():
    store = SQLiteStore(":memory:")
    precedent = CanonicalPrecedent(
        id="prec-1",
        source="bnp_pangea",
        court="STJ",
        precedent_type="RR",
        paradigm_cases=[ParadigmCase(number="123")],
    )
    document = CanonicalDocument(
        id="doc-1",
        source="tjsp_cjsg",
        document_type="acordao",
        text="Inteiro teor publico",
    )

    store.save_many([precedent, document])

    assert store.count() == 2
    assert store.count(source="bnp_pangea") == 1
    assert store.list_records(kind="precedent")[0]["precedent_type"] == "RR"
    assert store.list_records(source="tjsp_cjsg")[0]["document_type"] == "acordao"


def test_sqlite_store_query_records_with_structured_filters_and_stats():
    store = SQLiteStore(":memory:")
    first = CanonicalDecision(
        id="dec-1",
        source="tjsp_cjsg",
        court="TJSP",
        case_number="0003938-14.2017.8.26.0323",
        decision_type="acordao",
        subject="Homicidio Qualificado",
        rapporteur="Relator Exemplo",
        publication_date="2026-07-30",
    )
    second = CanonicalDecision(
        id="dec-2",
        source="tjsp_cjsg",
        court="TJSP",
        case_number="0000000-00.2020.8.26.0000",
        decision_type="acordao",
        subject="Roubo",
        rapporteur="Outro Relator",
        publication_date="2025-01-10",
    )

    store.save_many([first, second])

    results = store.query_records(
        kind="decision",
        court="TJSP",
        subject="Homicidio Qualificado",
        publication_date_from="2026-01-01",
    )
    stats = store.stats()

    assert [record["id"] for record in results] == ["dec-1"]
    assert stats.total == 2
    assert stats.by_kind == {"decision": 2}
    assert stats.by_source == {"tjsp_cjsg": 2}


def test_sqlite_store_upserts_records():
    store = SQLiteStore(":memory:")
    original = CanonicalDecision(id="dec-1", source="tjsp_cjsg", court="TJSP", summary="old")
    updated = CanonicalDecision(id="dec-1", source="tjsp_cjsg", court="TJSP", summary="new")

    store.save(original)
    store.save(updated)

    assert store.count() == 1
    assert store.get("decision", "dec-1")["summary"] == "new"


def test_sqlite_store_deduplicates_by_canonical_key():
    store = SQLiteStore(":memory:")
    original = CanonicalDecision(
        id="dec-original",
        source="tjsp_cjsg",
        court="TJSP",
        case_number="0003938-14.2017.8.26.0323",
        decision_type="acordao",
        summary="old",
    )
    duplicate = CanonicalDecision(
        id="dec-duplicate",
        source="tjsp_cjsg",
        court="TJSP",
        case_number="0003938-14.2017.8.26.0323",
        decision_type="acordao",
        summary="new",
    )

    store.save(original)
    store.save(duplicate)

    assert store.count() == 1
    assert store.get("decision", "dec-original") is None
    assert store.get("decision", "dec-duplicate")["summary"] == "new"


def test_sqlite_store_queries_by_canonical_key():
    store = SQLiteStore(":memory:")
    decision = CanonicalDecision(
        id="dec-1",
        source="tjsp_cjsg",
        court="TJSP",
        case_number="0003938-14.2017.8.26.0323",
        decision_type="acordao",
    )

    store.save(decision)
    results = store.query_records(
        canonical_key="decision|tjsp_cjsg|tjsp|0003938-14.2017.8.26.0323|acordao"
    )

    assert [record["id"] for record in results] == ["dec-1"]


def test_sqlite_store_saves_and_lists_research_runs():
    store = SQLiteStore(":memory:")
    decision = CanonicalDecision(
        id="dec-1",
        source="tjsp_cjsg",
        court="TJSP",
        case_number="0003938-14.2017.8.26.0323",
        decision_type="acordao",
    )

    run = store.save_research_run(
        source="tjsp_cjsg",
        text="homicidio qualificado",
        query={"page": 1, "page_size": 10},
        records=[decision],
        label="Carteira criminal",
    )

    stored_run = store.get_research_run(run.id)
    runs = store.list_research_runs()
    records = store.get_research_run_records(run.id)

    assert run.id.startswith("run-")
    assert run.record_count == 1
    assert stored_run is not None
    assert stored_run["label"] == "Carteira criminal"
    assert stored_run["query"] == {"page": 1, "page_size": 10}
    assert [item["id"] for item in runs] == [run.id]
    assert [record["id"] for record in records] == ["dec-1"]


def test_sqlite_store_research_run_records_follow_canonical_deduplication():
    store = SQLiteStore(":memory:")
    original = CanonicalDecision(
        id="dec-original",
        source="tjsp_cjsg",
        court="TJSP",
        case_number="0003938-14.2017.8.26.0323",
        decision_type="acordao",
    )
    duplicate = CanonicalDecision(
        id="dec-duplicate",
        source="tjsp_cjsg",
        court="TJSP",
        case_number="0003938-14.2017.8.26.0323",
        decision_type="acordao",
    )

    run = store.save_research_run(
        source="tjsp_cjsg",
        text="homicidio qualificado",
        query={},
        records=[original, duplicate],
    )

    records = store.get_research_run_records(run.id)

    assert run.record_count == 2
    assert [record["id"] for record in records] == ["dec-duplicate"]


def test_sqlite_store_paginates_research_run_records():
    store = SQLiteStore(":memory:")
    records = [
        CanonicalDecision(
            id=f"dec-{index}",
            source="tjsp_cjsg",
            court="TJSP",
            case_number=f"0000000-00.2026.8.26.{index:04d}",
            decision_type="acordao",
            publication_date=f"2026-08-0{index}",
        )
        for index in range(1, 4)
    ]
    run = store.save_research_run(
        source="tjsp_cjsg",
        text="homicidio qualificado",
        query={},
        records=records,
    )

    first_page = store.get_research_run_records(run.id, limit=2)
    second_page = store.get_research_run_records(run.id, limit=2, offset=2)

    assert store.count_research_run_records(run.id) == 3
    assert [record["id"] for record in first_page] == ["dec-3", "dec-2"]
    assert [record["id"] for record in second_page] == ["dec-1"]
