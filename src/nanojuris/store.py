"""Local storage backends for canonical extraction records."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Literal, Protocol
from uuid import uuid4

from nanojuris.canonical import normalize_date
from nanojuris.models import CanonicalDecision, CanonicalDocument, CanonicalPrecedent, utc_now_iso

StoredRecordKind = Literal["decision", "document", "precedent"]
CanonicalRecord = CanonicalDecision | CanonicalDocument | CanonicalPrecedent


class CanonicalStore(Protocol):
    """Store contract shared by SQLite and future production backends."""

    def save(self, record: CanonicalRecord) -> None:
        """Persist one canonical record."""

    def save_many(self, records: Iterable[CanonicalRecord]) -> None:
        """Persist canonical records."""

    def get(self, kind: StoredRecordKind, record_id: str) -> dict[str, Any] | None:
        """Return one stored canonical record as a dictionary."""

    def query_records(
        self,
        *,
        kind: StoredRecordKind | None = None,
        source: str | None = None,
        court: str | None = None,
        case_number: str | None = None,
        subject: str | None = None,
        rapporteur: str | None = None,
        decision_type: str | None = None,
        precedent_type: str | None = None,
        canonical_key: str | None = None,
        publication_date_from: str | None = None,
        publication_date_to: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Query stored records with structured filters."""

    def count_records(
        self,
        *,
        kind: StoredRecordKind | None = None,
        source: str | None = None,
        court: str | None = None,
        case_number: str | None = None,
        subject: str | None = None,
        rapporteur: str | None = None,
        decision_type: str | None = None,
        precedent_type: str | None = None,
        canonical_key: str | None = None,
        publication_date_from: str | None = None,
        publication_date_to: str | None = None,
    ) -> int:
        """Count records matching the structured query filters."""

    def stats(self) -> StoreStats:
        """Return aggregate counts for stored records."""


@dataclass(slots=True)
class StoreStats:
    """Aggregate counts for stored canonical records."""

    total: int
    by_kind: dict[str, int]
    by_source: dict[str, int]

    @property
    def decisions(self) -> int:
        """Backward-compatible count for decision records."""

        return int(self.by_kind.get("decision", 0))

    @property
    def precedents(self) -> int:
        """Convenience count for precedent records."""

        return int(self.by_kind.get("precedent", 0))

    @property
    def documents(self) -> int:
        """Convenience count for document records."""

        return int(self.by_kind.get("document", 0))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ResearchRun:
    """A saved search run linked to canonical records."""

    id: str
    source: str
    text: str
    query: dict[str, Any]
    record_count: int
    created_at: str
    label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SourceSyncManifest:
    """Audit manifest for one synchronized public resource."""

    source: str
    dataset_id: str
    resource_id: str
    format: str
    source_url: str | None
    source_hash: str | None
    source_fingerprint: str | None
    content_sha256: str
    response_bytes: int
    records_seen: int
    records_saved: int
    duplicate_records: int
    invalid_records: int
    run_id: str
    status: str
    synced_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SQLiteStore:
    """SQLite-backed store for canonical extraction records."""

    def __init__(self, path: str | Path | sqlite3.Connection) -> None:
        self._owns_connection = not isinstance(path, sqlite3.Connection)
        self.connection = path if isinstance(path, sqlite3.Connection) else sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.initialize()

    def initialize(self) -> None:
        """Create the storage schema when it does not exist."""

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS canonical_records (
                kind TEXT NOT NULL,
                id TEXT NOT NULL,
                source TEXT NOT NULL,
                court TEXT,
                case_number TEXT,
                subject TEXT,
                rapporteur TEXT,
                decision_type TEXT,
                precedent_type TEXT,
                publication_date TEXT,
                document_type TEXT,
                canonical_key TEXT,
                record_json TEXT NOT NULL,
                source_trace_json TEXT,
                extraction_trace_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (kind, id)
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS research_runs (
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
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS research_run_records (
                run_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                record_id TEXT NOT NULL,
                canonical_key TEXT NOT NULL,
                PRIMARY KEY (run_id, canonical_key),
                FOREIGN KEY (run_id) REFERENCES research_runs(id)
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS source_sync_manifests (
                source TEXT NOT NULL,
                dataset_id TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                format TEXT NOT NULL,
                source_url TEXT,
                source_hash TEXT,
                source_fingerprint TEXT,
                content_sha256 TEXT NOT NULL,
                response_bytes INTEGER NOT NULL,
                records_seen INTEGER NOT NULL,
                records_saved INTEGER NOT NULL,
                duplicate_records INTEGER NOT NULL,
                invalid_records INTEGER NOT NULL,
                run_id TEXT NOT NULL,
                status TEXT NOT NULL,
                synced_at TEXT NOT NULL,
                PRIMARY KEY (source, dataset_id, resource_id),
                FOREIGN KEY (run_id) REFERENCES research_runs(id)
            )
            """
        )
        self._add_table_column_if_missing("source_sync_manifests", "source_fingerprint TEXT")
        for column in (
            "subject TEXT",
            "rapporteur TEXT",
            "decision_type TEXT",
            "precedent_type TEXT",
            "publication_date TEXT",
            "canonical_key TEXT",
        ):
            self._add_column_if_missing(column)
        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_records_source
            ON canonical_records (source)
            """
        )
        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_records_case_number
            ON canonical_records (case_number)
            """
        )
        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_canonical_records_court
            ON canonical_records (court)
            """
        )
        self.connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_canonical_records_canonical_key
            ON canonical_records (canonical_key)
            WHERE canonical_key IS NOT NULL
            """
        )
        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_research_runs_created_at
            ON research_runs (created_at)
            """
        )
        self.connection.commit()

    def save(self, record: CanonicalRecord) -> None:
        """Insert or replace one canonical record."""

        self.save_many([record])

    def save_many(self, records: Iterable[CanonicalRecord]) -> None:
        """Insert or replace canonical records in one transaction."""

        now = utc_now_iso()
        rows = [_record_to_row(record, now=now) for record in records]
        if not rows:
            return
        with self.connection:
            self._save_rows(rows)

    def _save_rows(self, rows: list[tuple[object, ...]]) -> None:
        self.connection.executemany(
            """
            INSERT INTO canonical_records (
                kind,
                id,
                source,
                court,
                case_number,
                subject,
                rapporteur,
                decision_type,
                precedent_type,
                publication_date,
                document_type,
                canonical_key,
                record_json,
                source_trace_json,
                extraction_trace_json,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT DO UPDATE SET
                kind = excluded.kind,
                id = excluded.id,
                source = excluded.source,
                court = excluded.court,
                case_number = excluded.case_number,
                subject = excluded.subject,
                rapporteur = excluded.rapporteur,
                decision_type = excluded.decision_type,
                precedent_type = excluded.precedent_type,
                publication_date = excluded.publication_date,
                document_type = excluded.document_type,
                canonical_key = excluded.canonical_key,
                record_json = excluded.record_json,
                source_trace_json = excluded.source_trace_json,
                extraction_trace_json = excluded.extraction_trace_json,
                updated_at = excluded.updated_at
            """,
            rows,
        )

    def get(self, kind: StoredRecordKind, record_id: str) -> dict[str, Any] | None:
        """Return one stored canonical record as a dictionary."""

        row = self.connection.execute(
            """
            SELECT record_json FROM canonical_records
            WHERE kind = ? AND id = ?
            """,
            (kind, record_id),
        ).fetchone()
        if row is None:
            return None
        return json.loads(str(row["record_json"]))

    def list_records(
        self,
        *,
        kind: StoredRecordKind | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List stored records as dictionaries."""

        clauses: list[str] = []
        params: list[object] = []
        if kind:
            clauses.append("kind = ?")
            params.append(kind)
        if source:
            clauses.append("source = ?")
            params.append(source)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(max(1, limit))
        rows = self.connection.execute(
            f"""
            SELECT record_json FROM canonical_records
            {where}
            ORDER BY updated_at DESC, id ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [json.loads(str(row["record_json"])) for row in rows]

    def query_records(
        self,
        *,
        kind: StoredRecordKind | None = None,
        source: str | None = None,
        court: str | None = None,
        case_number: str | None = None,
        subject: str | None = None,
        rapporteur: str | None = None,
        decision_type: str | None = None,
        precedent_type: str | None = None,
        canonical_key: str | None = None,
        publication_date_from: str | None = None,
        publication_date_to: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Query a bounded page of records with structured extraction filters."""

        where, params = _record_query_components(
            kind=kind,
            source=source,
            court=court,
            case_number=case_number,
            subject=subject,
            rapporteur=rapporteur,
            decision_type=decision_type,
            precedent_type=precedent_type,
            canonical_key=canonical_key,
            publication_date_from=publication_date_from,
            publication_date_to=publication_date_to,
        )
        params.extend([max(1, limit), max(0, offset)])
        rows = self.connection.execute(
            f"""
            SELECT record_json FROM canonical_records
            {where}
            ORDER BY publication_date DESC, updated_at DESC, id ASC
            LIMIT ?
            OFFSET ?
            """,
            params,
        ).fetchall()
        return [json.loads(str(row["record_json"])) for row in rows]

    def count_records(
        self,
        *,
        kind: StoredRecordKind | None = None,
        source: str | None = None,
        court: str | None = None,
        case_number: str | None = None,
        subject: str | None = None,
        rapporteur: str | None = None,
        decision_type: str | None = None,
        precedent_type: str | None = None,
        canonical_key: str | None = None,
        publication_date_from: str | None = None,
        publication_date_to: str | None = None,
    ) -> int:
        """Count records matching the same filters accepted by query_records."""

        where, params = _record_query_components(
            kind=kind,
            source=source,
            court=court,
            case_number=case_number,
            subject=subject,
            rapporteur=rapporteur,
            decision_type=decision_type,
            precedent_type=precedent_type,
            canonical_key=canonical_key,
            publication_date_from=publication_date_from,
            publication_date_to=publication_date_to,
        )
        row = self.connection.execute(
            f"SELECT COUNT(*) AS total FROM canonical_records {where}",
            params,
        ).fetchone()
        return int(row["total"] if row is not None else 0)

    def stats(self) -> StoreStats:
        """Return aggregate counts for stored records."""

        return StoreStats(
            total=self.count(),
            by_kind=self._count_by("kind"),
            by_source=self._count_by("source"),
        )

    def count(self, *, kind: StoredRecordKind | None = None, source: str | None = None) -> int:
        """Count stored records."""

        clauses: list[str] = []
        params: list[object] = []
        if kind:
            clauses.append("kind = ?")
            params.append(kind)
        if source:
            clauses.append("source = ?")
            params.append(source)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        row = self.connection.execute(
            f"SELECT COUNT(*) AS total FROM canonical_records {where}",
            params,
        ).fetchone()
        return int(row["total"] if row is not None else 0)

    def save_research_run(
        self,
        *,
        source: str,
        text: str,
        query: dict[str, Any],
        records: Iterable[CanonicalRecord],
        label: str | None = None,
        sync_manifest: dict[str, Any] | None = None,
    ) -> ResearchRun:
        """Persist a saved search run and link it to canonical records."""

        now = utc_now_iso()
        run = ResearchRun(
            id=f"run-{uuid4().hex}",
            source=source,
            text=text,
            query=query,
            record_count=0,
            created_at=now,
            label=label,
        )
        record_list = list(records)
        rows = []
        for record in record_list:
            kind = _record_kind(record)
            rows.append((run.id, kind, record.id, _canonical_key(record, kind=kind)))
        record_rows = [_record_to_row(record, now=now) for record in record_list]
        with self.connection:
            self._save_rows(record_rows)
            self.connection.execute(
                """
                INSERT INTO research_runs (
                    id, source, text, query_json, record_count, label, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.source,
                    run.text,
                    json.dumps(run.query, ensure_ascii=False, sort_keys=True),
                    len(rows),
                    run.label,
                    run.created_at,
                ),
            )
            if rows:
                self.connection.executemany(
                    """
                    INSERT OR REPLACE INTO research_run_records (
                        run_id, kind, record_id, canonical_key
                    ) VALUES (?, ?, ?, ?)
                    """,
                    rows,
                )
            if sync_manifest is not None:
                self._save_sync_manifest(sync_manifest, run_id=run.id, synced_at=now)
        run.record_count = len(rows)
        return run

    def get_sync_manifest(
        self,
        *,
        source: str,
        dataset_id: str,
        resource_id: str,
    ) -> dict[str, Any] | None:
        """Return the latest successful manifest for one public resource."""

        row = self.connection.execute(
            """
            SELECT * FROM source_sync_manifests
            WHERE source = ? AND dataset_id = ? AND resource_id = ?
            """,
            (source, dataset_id, resource_id),
        ).fetchone()
        return _sync_manifest_row_to_dict(row) if row is not None else None

    def list_sync_manifests(
        self,
        *,
        source: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List resource manifests, newest synchronization first."""

        if source:
            rows = self.connection.execute(
                """
                SELECT * FROM source_sync_manifests
                WHERE source = ?
                ORDER BY synced_at DESC, dataset_id ASC, resource_id ASC
                LIMIT ?
                """,
                (source, max(1, limit)),
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT * FROM source_sync_manifests
                ORDER BY synced_at DESC, source ASC, dataset_id ASC, resource_id ASC
                LIMIT ?
                """,
                (max(1, limit),),
            ).fetchall()
        return [_sync_manifest_row_to_dict(row) for row in rows]

    def _save_sync_manifest(
        self,
        manifest: dict[str, Any],
        *,
        run_id: str,
        synced_at: str,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO source_sync_manifests (
                source, dataset_id, resource_id, format, source_url, source_hash,
                source_fingerprint,
                content_sha256, response_bytes, records_seen, records_saved,
                duplicate_records, invalid_records, run_id, status, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (source, dataset_id, resource_id) DO UPDATE SET
                format = excluded.format,
                source_url = excluded.source_url,
                source_hash = excluded.source_hash,
                source_fingerprint = excluded.source_fingerprint,
                content_sha256 = excluded.content_sha256,
                response_bytes = excluded.response_bytes,
                records_seen = excluded.records_seen,
                records_saved = excluded.records_saved,
                duplicate_records = excluded.duplicate_records,
                invalid_records = excluded.invalid_records,
                run_id = excluded.run_id,
                status = excluded.status,
                synced_at = excluded.synced_at
            """,
            (
                str(manifest["source"]),
                str(manifest["dataset_id"]),
                str(manifest["resource_id"]),
                str(manifest["format"]),
                manifest.get("source_url"),
                manifest.get("source_hash"),
                manifest.get("source_fingerprint"),
                str(manifest["content_sha256"]),
                int(manifest["response_bytes"]),
                int(manifest["records_seen"]),
                int(manifest["records_saved"]),
                int(manifest["duplicate_records"]),
                int(manifest["invalid_records"]),
                run_id,
                str(manifest.get("status") or "complete"),
                synced_at,
            ),
        )

    def get_research_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one saved search run."""

        row = self.connection.execute(
            """
            SELECT * FROM research_runs
            WHERE id = ?
            """,
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return _run_row_to_dict(row)

    def list_research_runs(self, *, limit: int = 50) -> list[dict[str, Any]]:
        """List saved search runs."""

        rows = self.connection.execute(
            """
            SELECT * FROM research_runs
            ORDER BY created_at DESC, id ASC
            LIMIT ?
            """,
            (max(1, limit),),
        ).fetchall()
        return [_run_row_to_dict(row) for row in rows]

    def get_research_run_records(
        self,
        run_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Return canonical records linked to a saved search run."""

        rows = self.connection.execute(
            """
            SELECT cr.record_json
            FROM research_run_records rrr
            JOIN canonical_records cr ON cr.canonical_key = rrr.canonical_key
            WHERE rrr.run_id = ?
            ORDER BY cr.publication_date DESC, cr.updated_at DESC, cr.id ASC
            LIMIT ? OFFSET ?
            """,
            (run_id, max(1, limit), max(0, offset)),
        ).fetchall()
        return [json.loads(str(row["record_json"])) for row in rows]

    def count_research_run_records(self, run_id: str) -> int:
        """Count canonical records linked to a saved search run."""

        row = self.connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM research_run_records
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()
        return int(row["total"] if row is not None else 0)

    def close(self) -> None:
        """Close the underlying connection when owned by the store."""

        if self._owns_connection:
            self.connection.close()

    def __enter__(self) -> SQLiteStore:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    def _add_column_if_missing(self, column_definition: str) -> None:
        column_name = column_definition.split(" ", 1)[0]
        existing = {
            str(row["name"])
            for row in self.connection.execute("PRAGMA table_info(canonical_records)").fetchall()
        }
        if column_name not in existing:
            self.connection.execute(f"ALTER TABLE canonical_records ADD COLUMN {column_definition}")

    def _add_table_column_if_missing(self, table: str, column_definition: str) -> None:
        column_name = column_definition.split(" ", 1)[0]
        existing = {
            str(row["name"])
            for row in self.connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column_name not in existing:
            self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {column_definition}")

    def _count_by(self, column: str) -> dict[str, int]:
        rows = self.connection.execute(
            f"""
            SELECT {column} AS key, COUNT(*) AS total
            FROM canonical_records
            GROUP BY {column}
            ORDER BY {column}
            """
        ).fetchall()
        return {str(row["key"]): int(row["total"]) for row in rows if row["key"] is not None}


def _record_to_row(record: CanonicalRecord, *, now: str) -> tuple[object, ...]:
    kind = _record_kind(record)
    payload = _to_jsonable(record)
    source_trace = payload.get("source_trace")
    extraction_trace = payload.get("extraction_trace")
    return (
        kind,
        record.id,
        record.source,
        getattr(record, "court", None),
        getattr(record, "case_number", None),
        getattr(record, "subject", None),
        getattr(record, "rapporteur", None),
        getattr(record, "decision_type", None),
        getattr(record, "precedent_type", None),
        _storage_date(
            getattr(record, "publication_date", None) or getattr(record, "updated_at", None)
        ),
        getattr(record, "document_type", None),
        _canonical_key(record, kind=kind),
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        json.dumps(source_trace, ensure_ascii=False, sort_keys=True) if source_trace else None,
        json.dumps(extraction_trace, ensure_ascii=False, sort_keys=True)
        if extraction_trace
        else None,
        now,
        now,
    )


def _record_kind(record: CanonicalRecord) -> StoredRecordKind:
    if isinstance(record, CanonicalDecision):
        return "decision"
    if isinstance(record, CanonicalDocument):
        return "document"
    return "precedent"


def _record_query_components(
    *,
    kind: StoredRecordKind | None = None,
    source: str | None = None,
    court: str | None = None,
    case_number: str | None = None,
    subject: str | None = None,
    rapporteur: str | None = None,
    decision_type: str | None = None,
    precedent_type: str | None = None,
    canonical_key: str | None = None,
    publication_date_from: str | None = None,
    publication_date_to: str | None = None,
) -> tuple[str, list[object]]:
    """Build one SQL predicate for both paged reads and matching counts."""

    filters = {
        "kind": kind,
        "source": source,
        "court": court,
        "case_number": case_number,
        "subject": subject,
        "rapporteur": rapporteur,
        "decision_type": decision_type,
        "precedent_type": precedent_type,
        "canonical_key": canonical_key,
    }
    clauses: list[str] = []
    params: list[object] = []
    for column, value in filters.items():
        if value:
            clauses.append(f"{column} = ?")
            params.append(value)
    if publication_date_from:
        clauses.append("publication_date >= ?")
        params.append(_required_storage_date(publication_date_from))
    if publication_date_to:
        clauses.append("publication_date <= ?")
        params.append(_required_storage_date(publication_date_to))
    return (f"WHERE {' AND '.join(clauses)}" if clauses else ""), params


def _canonical_key(record: CanonicalRecord, *, kind: StoredRecordKind) -> str:
    if isinstance(record, CanonicalDecision):
        return _join_key(
            kind,
            record.source,
            record.court,
            record.case_number or record.registry_number or record.id,
            record.decision_type or "decision",
        )
    if isinstance(record, CanonicalPrecedent):
        return _join_key(
            kind,
            record.source,
            record.court,
            record.precedent_type,
            str(record.number or record.id),
        )
    return _join_key(
        kind,
        record.source,
        record.document_type,
        record.sha256 or record.url or record.id,
    )


def _join_key(*parts: str) -> str:
    return "|".join(_normalize_key_part(part) for part in parts if part)


def _normalize_key_part(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def _storage_date(value: object) -> str | None:
    """Store comparable dates in ISO form while retaining raw data in JSON."""

    if value is None:
        return None
    normalized = normalize_date(value)
    return normalized or str(value).strip() or None


def _required_storage_date(value: str) -> str:
    normalized = normalize_date(value)
    if normalized is None:
        raise ValueError("filtros de data devem usar YYYY-MM-DD ou DD/MM/YYYY")
    return normalized


def _run_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "source": str(row["source"]),
        "text": str(row["text"]),
        "query": json.loads(str(row["query_json"])),
        "record_count": int(row["record_count"]),
        "label": row["label"],
        "created_at": str(row["created_at"]),
    }


def _sync_manifest_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "source": str(row["source"]),
        "dataset_id": str(row["dataset_id"]),
        "resource_id": str(row["resource_id"]),
        "format": str(row["format"]),
        "source_url": row["source_url"],
        "source_hash": row["source_hash"],
        "source_fingerprint": row["source_fingerprint"],
        "content_sha256": str(row["content_sha256"]),
        "response_bytes": int(row["response_bytes"]),
        "records_seen": int(row["records_seen"]),
        "records_saved": int(row["records_saved"]),
        "duplicate_records": int(row["duplicate_records"]),
        "invalid_records": int(row["invalid_records"]),
        "run_id": str(row["run_id"]),
        "status": str(row["status"]),
        "synced_at": str(row["synced_at"]),
    }


def _to_jsonable(value: object) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _to_jsonable(value.to_dict())
    if is_dataclass(value) and not isinstance(value, type):
        return _to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    return value
