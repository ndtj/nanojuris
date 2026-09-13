"""Local storage backends for canonical extraction records."""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Literal, Protocol
from urllib.parse import urlparse
from uuid import uuid4

from nanojuris.canonical import normalize_date
from nanojuris.identity import canonical_record_identity
from nanojuris.models import CanonicalDecision, CanonicalDocument, CanonicalPrecedent, utc_now_iso

StoredRecordKind = Literal["decision", "document", "precedent"]
CanonicalRecord = CanonicalDecision | CanonicalDocument | CanonicalPrecedent
TombstoneEvidenceType = Literal[
    "official_tombstone",
    "official_absence_manifest",
    "explicit_retraction",
]


class CanonicalStore(Protocol):
    """Store contract shared by SQLite and future production backends."""

    def save(self, record: CanonicalRecord) -> None:
        """Persist one canonical record."""

    def save_many(self, records: Iterable[CanonicalRecord]) -> None:
        """Persist canonical records."""

    def get(self, kind: StoredRecordKind, record_id: str) -> dict[str, Any] | None:
        """Return one stored canonical record as a dictionary."""

    def get_identity(self, kind: StoredRecordKind, record_id: str) -> dict[str, Any] | None:
        """Return the explainable legal identity stored with a record."""

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
        case_class: str | None = None,
        judging_body: str | None = None,
        degree: str | None = None,
        instance: str | None = None,
        branch: str | None = None,
        legal_area: str | None = None,
        authority: str | None = None,
        collection: str | None = None,
        document_type: str | None = None,
        source_origin: str | None = None,
        access_status: str | None = None,
        canonical_key: str | None = None,
        publication_date_from: str | None = None,
        publication_date_to: str | None = None,
        judgment_date_from: str | None = None,
        judgment_date_to: str | None = None,
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
        case_class: str | None = None,
        judging_body: str | None = None,
        degree: str | None = None,
        instance: str | None = None,
        branch: str | None = None,
        legal_area: str | None = None,
        authority: str | None = None,
        collection: str | None = None,
        document_type: str | None = None,
        source_origin: str | None = None,
        access_status: str | None = None,
        canonical_key: str | None = None,
        publication_date_from: str | None = None,
        publication_date_to: str | None = None,
        judgment_date_from: str | None = None,
        judgment_date_to: str | None = None,
    ) -> int:
        """Count records matching the structured query filters."""

    def stats(self) -> StoreStats:
        """Return aggregate counts for stored records."""

    def record_tombstone(self, evidence: TombstoneEvidence) -> dict[str, Any]:
        """Persist explicit source evidence without deleting the record."""

    def list_tombstones(
        self,
        *,
        source: str | None = None,
        canonical_key: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List source-proven removal evidence."""


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
    """A saved search run linked to canonical records.

    ``record_count`` is the number of canonical records submitted by the
    search operation before the run-link deduplication step.  The distinct
    records actually linked to this run are exposed as
    ``persisted_record_count``.  Keeping both values prevents a duplicate
    input from being mistaken for data loss while preserving the historical
    meaning of ``record_count``.
    """

    id: str
    source: str
    text: str
    query: dict[str, Any]
    record_count: int
    created_at: str
    label: str | None = None
    # Appended with a default so callers using the historical positional
    # constructor remain source-compatible.
    persisted_record_count: int = 0
    manifest: dict[str, Any] | None = None

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


@dataclass(frozen=True, slots=True)
class TombstoneEvidence:
    """Explicit, provenance-backed evidence that a source removed a record.

    Creating a tombstone never removes or hides the canonical record.  The
    evidence URL must be HTTPS and its content hash is normalized to the
    ``sha256:<hex>`` form so that independent observations remain comparable.
    Absence from a search result is deliberately not accepted as evidence.
    """

    source: str
    canonical_key: str
    evidence_url: str
    evidence_sha256: str
    evidence_type: TombstoneEvidenceType
    observed_at: str
    reason: str
    schema_version: str = "nanojuris-tombstone-evidence-v1"

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.canonical_key.strip():
            raise ValueError("source e canonical_key são obrigatórios")
        parsed = urlparse(self.evidence_url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("evidence_url deve ser uma URL HTTPS pública")
        digest = self.evidence_sha256.lower().removeprefix("sha256:")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("evidence_sha256 deve conter um SHA-256 hexadecimal")
        if self.evidence_type not in {
            "official_tombstone",
            "official_absence_manifest",
            "explicit_retraction",
        }:
            raise ValueError("evidence_type inválido")
        if not self.observed_at.strip() or not self.reason.strip():
            raise ValueError("observed_at e reason são obrigatórios")
        object.__setattr__(self, "evidence_sha256", f"sha256:{digest}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SQLiteStore:
    """SQLite-backed store for canonical extraction records."""

    def __init__(self, path: str | Path | sqlite3.Connection) -> None:
        self._owns_connection = not isinstance(path, sqlite3.Connection)
        self.connection = path if isinstance(path, sqlite3.Connection) else sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self._fts_enabled = False
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
                case_class TEXT,
                judging_body TEXT,
                degree TEXT,
                instance TEXT,
                branch TEXT,
                legal_area TEXT,
                authority TEXT,
                collection TEXT,
                source_origin TEXT,
                access_status TEXT,
                judgment_date TEXT,
                source_updated_at TEXT,
                publication_date TEXT,
                document_type TEXT,
                document_url TEXT,
                canonical_key TEXT,
                legal_identity_json TEXT,
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
                persisted_record_count INTEGER NOT NULL DEFAULT 0,
                label TEXT,
                manifest_json TEXT,
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
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS record_tombstones (
                source TEXT NOT NULL,
                canonical_key TEXT NOT NULL,
                evidence_url TEXT NOT NULL,
                evidence_sha256 TEXT NOT NULL,
                evidence_type TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (source, canonical_key, evidence_sha256)
            )
            """
        )
        # FTS5 is optional in some system SQLite builds.  The structured store
        # remains fully functional when the extension is unavailable, while
        # capable builds receive a synchronized full-text projection.
        try:
            self.connection.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS canonical_records_fts USING fts5(
                    record_key UNINDEXED,
                    kind UNINDEXED,
                    source UNINDEXED,
                    title,
                    body,
                    tokenize='unicode61'
                )
                """
            )
            self._fts_enabled = True
        except sqlite3.OperationalError:
            self._fts_enabled = False
        self._add_table_column_if_missing("source_sync_manifests", "source_fingerprint TEXT")
        self._add_table_column_if_missing(
            "research_runs", "persisted_record_count INTEGER NOT NULL DEFAULT 0"
        )
        self._add_table_column_if_missing("research_runs", "manifest_json TEXT")
        self.connection.execute(
            """
            UPDATE research_runs
            SET persisted_record_count = (
                SELECT COUNT(*) FROM research_run_records
                WHERE research_run_records.run_id = research_runs.id
            )
            WHERE persisted_record_count = 0
            """
        )
        for column in (
            "subject TEXT",
            "rapporteur TEXT",
            "decision_type TEXT",
            "precedent_type TEXT",
            "case_class TEXT",
            "judging_body TEXT",
            "degree TEXT",
            "instance TEXT",
            "branch TEXT",
            "legal_area TEXT",
            "authority TEXT",
            "collection TEXT",
            "source_origin TEXT",
            "access_status TEXT",
            "judgment_date TEXT",
            "source_updated_at TEXT",
            "publication_date TEXT",
            "document_url TEXT",
            "canonical_key TEXT",
            "legal_identity_json TEXT",
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
        for column in (
            "judgment_date",
            "source_updated_at",
            "case_class",
            "judging_body",
            "degree",
            "instance",
            "branch",
            "legal_area",
            "authority",
            "collection",
            "source_origin",
            "document_type",
            "document_url",
            "access_status",
        ):
            self.connection.execute(
                f"CREATE INDEX IF NOT EXISTS idx_canonical_records_{column} "
                f"ON canonical_records ({column})"
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
        if self._fts_enabled:
            self._backfill_fts_if_empty()

    def save(self, record: CanonicalRecord) -> None:
        """Insert or replace one canonical record."""

        self.save_many([record])

    def save_many(self, records: Iterable[CanonicalRecord]) -> None:
        """Insert or replace canonical records in one transaction."""

        now = utc_now_iso()
        record_list = list(records)
        rows = [_record_to_row(record, now=now) for record in record_list]
        if not rows:
            return
        with self.connection:
            self._save_rows(rows)
            self._sync_fts(records=record_list)

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
                case_class,
                judging_body,
                degree,
                instance,
                branch,
                legal_area,
                authority,
                collection,
                source_origin,
                access_status,
                judgment_date,
                source_updated_at,
                publication_date,
                document_type,
                document_url,
                canonical_key,
                legal_identity_json,
                record_json,
                source_trace_json,
                extraction_trace_json,
                created_at,
                updated_at
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?
            )
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
                case_class = excluded.case_class,
                judging_body = excluded.judging_body,
                degree = excluded.degree,
                instance = excluded.instance,
                branch = excluded.branch,
                legal_area = excluded.legal_area,
                authority = excluded.authority,
                collection = excluded.collection,
                source_origin = excluded.source_origin,
                access_status = excluded.access_status,
                judgment_date = excluded.judgment_date,
                source_updated_at = excluded.source_updated_at,
                publication_date = excluded.publication_date,
                document_type = excluded.document_type,
                document_url = excluded.document_url,
                canonical_key = excluded.canonical_key,
                legal_identity_json = excluded.legal_identity_json,
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
            SELECT record_json, legal_identity_json FROM canonical_records
            WHERE kind = ? AND id = ?
            """,
            (kind, record_id),
        ).fetchone()
        if row is None:
            return None
        return _decode_record_row(row)

    def get_identity(self, kind: StoredRecordKind, record_id: str) -> dict[str, Any] | None:
        """Return the explainable legal identity stored with a record."""

        row = self.connection.execute(
            """
            SELECT legal_identity_json FROM canonical_records
            WHERE kind = ? AND id = ?
            """,
            (kind, record_id),
        ).fetchone()
        if row is None or not row["legal_identity_json"]:
            return None
        return json.loads(str(row["legal_identity_json"]))

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
            SELECT record_json, legal_identity_json FROM canonical_records
            {where}
            ORDER BY updated_at DESC, id ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [_decode_record_row(row) for row in rows]

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
        case_class: str | None = None,
        judging_body: str | None = None,
        degree: str | None = None,
        instance: str | None = None,
        branch: str | None = None,
        legal_area: str | None = None,
        authority: str | None = None,
        collection: str | None = None,
        document_type: str | None = None,
        source_origin: str | None = None,
        access_status: str | None = None,
        canonical_key: str | None = None,
        publication_date_from: str | None = None,
        publication_date_to: str | None = None,
        judgment_date_from: str | None = None,
        judgment_date_to: str | None = None,
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
            case_class=case_class,
            judging_body=judging_body,
            degree=degree,
            instance=instance,
            branch=branch,
            legal_area=legal_area,
            authority=authority,
            collection=collection,
            document_type=document_type,
            source_origin=source_origin,
            access_status=access_status,
            canonical_key=canonical_key,
            publication_date_from=publication_date_from,
            publication_date_to=publication_date_to,
            judgment_date_from=judgment_date_from,
            judgment_date_to=judgment_date_to,
        )
        params.extend([max(1, limit), max(0, offset)])
        rows = self.connection.execute(
            f"""
            SELECT record_json, legal_identity_json FROM canonical_records
            {where}
            ORDER BY publication_date DESC, updated_at DESC, id ASC
            LIMIT ?
            OFFSET ?
            """,
            params,
        ).fetchall()
        return [_decode_record_row(row) for row in rows]

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
        case_class: str | None = None,
        judging_body: str | None = None,
        degree: str | None = None,
        instance: str | None = None,
        branch: str | None = None,
        legal_area: str | None = None,
        authority: str | None = None,
        collection: str | None = None,
        document_type: str | None = None,
        source_origin: str | None = None,
        access_status: str | None = None,
        canonical_key: str | None = None,
        publication_date_from: str | None = None,
        publication_date_to: str | None = None,
        judgment_date_from: str | None = None,
        judgment_date_to: str | None = None,
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
            case_class=case_class,
            judging_body=judging_body,
            degree=degree,
            instance=instance,
            branch=branch,
            legal_area=legal_area,
            authority=authority,
            collection=collection,
            document_type=document_type,
            source_origin=source_origin,
            access_status=access_status,
            canonical_key=canonical_key,
            publication_date_from=publication_date_from,
            publication_date_to=publication_date_to,
            judgment_date_from=judgment_date_from,
            judgment_date_to=judgment_date_to,
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
        manifest: dict[str, Any] | None = None,
    ) -> ResearchRun:
        """Persist a saved search run and link it to canonical records."""

        now = utc_now_iso()
        run = ResearchRun(
            id=f"run-{uuid4().hex}",
            source=source,
            text=text,
            query=query,
            record_count=0,
            persisted_record_count=0,
            created_at=now,
            label=label,
            manifest=manifest,
        )
        record_list = list(records)
        rows_by_key: dict[str, tuple[str, str, str, str]] = {}
        for record in record_list:
            kind = _record_kind(record)
            canonical_key = _canonical_key(record, kind=kind)
            rows_by_key[canonical_key] = (run.id, kind, record.id, canonical_key)
        rows = list(rows_by_key.values())
        record_rows = [_record_to_row(record, now=now) for record in record_list]
        with self.connection:
            self._save_rows(record_rows)
            self._sync_fts(records=record_list)
            self.connection.execute(
                """
                INSERT INTO research_runs (
                    id, source, text, query_json, record_count,
                    persisted_record_count, label, manifest_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.source,
                    run.text,
                    json.dumps(run.query, ensure_ascii=False, sort_keys=True),
                    len(record_list),
                    len(rows),
                    run.label,
                    json.dumps(_to_jsonable(run.manifest), ensure_ascii=False, sort_keys=True)
                    if run.manifest is not None
                    else None,
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
        run.record_count = len(record_list)
        run.persisted_record_count = len(rows)
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

    def record_tombstone(self, evidence: TombstoneEvidence) -> dict[str, Any]:
        """Record explicit removal evidence while retaining the source record.

        This operation is intentionally opt-in: callers must construct a
        validated :class:`TombstoneEvidence` from an official source artifact.
        No search result or synchronization diff is converted implicitly into a
        tombstone, and the canonical record is never deleted.
        """

        now = utc_now_iso()
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO record_tombstones (
                    source, canonical_key, evidence_url, evidence_sha256,
                    evidence_type, observed_at, reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (source, canonical_key, evidence_sha256) DO UPDATE SET
                    evidence_url = excluded.evidence_url,
                    evidence_type = excluded.evidence_type,
                    observed_at = excluded.observed_at,
                    reason = excluded.reason
                """,
                (
                    evidence.source,
                    evidence.canonical_key,
                    evidence.evidence_url,
                    evidence.evidence_sha256,
                    evidence.evidence_type,
                    evidence.observed_at,
                    evidence.reason,
                    now,
                ),
            )
        row = self.connection.execute(
            """
            SELECT * FROM record_tombstones
            WHERE source = ? AND canonical_key = ? AND evidence_sha256 = ?
            """,
            (evidence.source, evidence.canonical_key, evidence.evidence_sha256),
        ).fetchone()
        if row is None:  # pragma: no cover - defensive guard for unusual backends
            raise RuntimeError("tombstone não foi persistido")
        return _tombstone_row_to_dict(row)

    def list_tombstones(
        self,
        *,
        source: str | None = None,
        canonical_key: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List explicit tombstone evidence without filtering records out."""

        clauses: list[str] = []
        params: list[object] = []
        if source is not None:
            clauses.append("source = ?")
            params.append(source)
        if canonical_key is not None:
            clauses.append("canonical_key = ?")
            params.append(canonical_key)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(max(1, limit))
        rows = self.connection.execute(
            f"""
            SELECT * FROM record_tombstones
            {where}
            ORDER BY observed_at DESC, source ASC, canonical_key ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [_tombstone_row_to_dict(row) for row in rows]

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
            SELECT cr.record_json, cr.legal_identity_json
            FROM research_run_records rrr
            JOIN canonical_records cr ON cr.canonical_key = rrr.canonical_key
            WHERE rrr.run_id = ?
            ORDER BY cr.publication_date DESC, cr.updated_at DESC, cr.id ASC
            LIMIT ? OFFSET ?
            """,
            (run_id, max(1, limit), max(0, offset)),
        ).fetchall()
        return [_decode_record_row(row) for row in rows]

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

    def search_full_text(
        self,
        query: str,
        *,
        kind: StoredRecordKind | None = None,
        source: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Search canonical title/body text when SQLite FTS5 is available.

        FTS is a projection, never the source of truth: returned rows are
        joined back to ``canonical_records`` so callers receive the canonical
        JSON and identity envelope.  Unsupported SQLite builds return an empty
        list rather than pretending that no legal records match.
        """

        if not query or not query.strip() or not self._fts_enabled:
            return []
        # SQLite requires the virtual-table name (not an alias) on the left
        # side of MATCH for this FTS5 configuration.
        clauses = ["canonical_records_fts MATCH ?"]
        params: list[object] = [query.strip()]
        if kind:
            clauses.append("fts.kind = ?")
            params.append(kind)
        if source:
            clauses.append("fts.source = ?")
            params.append(source)
        params.extend([max(1, limit), max(0, offset)])
        try:
            rows = self.connection.execute(
                f"""
                SELECT cr.record_json, cr.legal_identity_json
                FROM canonical_records_fts fts
                JOIN canonical_records cr
                  ON cr.kind || ':' || cr.id = fts.record_key
                WHERE {" AND ".join(clauses)}
                ORDER BY bm25(canonical_records_fts), cr.publication_date DESC, cr.id ASC
                LIMIT ? OFFSET ?
                """,
                params,
            ).fetchall()
        except sqlite3.OperationalError as exc:
            # Malformed MATCH syntax is a query error, not a source-empty
            # result.  Preserve that distinction for callers and telemetry.
            raise ValueError("consulta FTS inválida") from exc
        return [_decode_record_row(row) for row in rows]

    def _sync_fts(self, *, records: list[CanonicalRecord]) -> None:
        if not self._fts_enabled:
            return
        for record in records:
            kind = _record_kind(record)
            key = f"{kind}:{record.id}"
            title, body = _record_text_for_fts(record)
            self.connection.execute(
                "DELETE FROM canonical_records_fts WHERE record_key = ?", (key,)
            )
            self.connection.execute(
                """
                INSERT INTO canonical_records_fts (record_key, kind, source, title, body)
                VALUES (?, ?, ?, ?, ?)
                """,
                (key, kind, record.source, title, body),
            )

    def _backfill_fts_if_empty(self) -> None:
        if not self._fts_enabled:
            return
        row = self.connection.execute(
            "SELECT COUNT(*) AS total FROM canonical_records_fts"
        ).fetchone()
        if row is None or int(row["total"]) > 0:
            return
        rows = self.connection.execute(
            "SELECT kind, id, source, record_json FROM canonical_records"
        ).fetchall()
        with self.connection:
            for item in rows:
                payload = json.loads(str(item["record_json"]))
                title, body = _payload_text_for_fts(payload)
                self.connection.execute(
                    """
                    INSERT INTO canonical_records_fts (record_key, kind, source, title, body)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        f"{item['kind']}:{item['id']}",
                        item["kind"],
                        item["source"],
                        title,
                        body,
                    ),
                )

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
    legal_identity = canonical_record_identity(record).to_dict()
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
        getattr(record, "case_class", None),
        getattr(record, "judging_body", None),
        getattr(record, "degree", None),
        getattr(record, "instance", None),
        getattr(record, "branch", None),
        getattr(record, "legal_area", None),
        getattr(record, "authority", None),
        getattr(record, "collection", None),
        getattr(record, "source_origin", None),
        _enum_value(getattr(record, "access_status", None)),
        _storage_date(getattr(record, "judgment_date", None)),
        _storage_date(getattr(record, "source_updated_at", None)),
        _storage_date(
            getattr(record, "publication_date", None) or getattr(record, "updated_at", None)
        ),
        getattr(record, "document_type", None),
        getattr(record, "document_url", None) or getattr(record, "url", None),
        _canonical_key(record, kind=kind),
        json.dumps(legal_identity, ensure_ascii=False, sort_keys=True),
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        json.dumps(source_trace, ensure_ascii=False, sort_keys=True) if source_trace else None,
        json.dumps(extraction_trace, ensure_ascii=False, sort_keys=True)
        if extraction_trace
        else None,
        now,
        now,
    )


def _decode_record_row(row: sqlite3.Row) -> dict[str, Any]:
    """Decode a stored record and attach identity without changing legacy fields."""

    payload = json.loads(str(row["record_json"]))
    identity_json = row["legal_identity_json"]
    if identity_json:
        payload["legal_identity"] = json.loads(str(identity_json))
    return payload


def _record_kind(record: CanonicalRecord) -> StoredRecordKind:
    if isinstance(record, CanonicalDecision):
        return "decision"
    if isinstance(record, CanonicalDocument):
        return "document"
    return "precedent"


def _record_text_for_fts(record: CanonicalRecord) -> tuple[str, str]:
    return _payload_text_for_fts(_to_jsonable(record))


def _payload_text_for_fts(payload: dict[str, Any]) -> tuple[str, str]:
    """Select legal text fields without indexing raw transport metadata."""

    title = " ".join(
        str(payload.get(name) or "").strip()
        for name in ("title", "subject", "case_class", "decision_type", "precedent_type")
        if str(payload.get(name) or "").strip()
    )
    body = " ".join(
        str(payload.get(name) or "").strip()
        for name in ("summary", "full_text", "text", "question", "thesis")
        if str(payload.get(name) or "").strip()
    )
    return title, body


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
    case_class: str | None = None,
    judging_body: str | None = None,
    degree: str | None = None,
    instance: str | None = None,
    branch: str | None = None,
    legal_area: str | None = None,
    authority: str | None = None,
    collection: str | None = None,
    document_type: str | None = None,
    source_origin: str | None = None,
    access_status: str | None = None,
    canonical_key: str | None = None,
    publication_date_from: str | None = None,
    publication_date_to: str | None = None,
    judgment_date_from: str | None = None,
    judgment_date_to: str | None = None,
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
        "case_class": case_class,
        "judging_body": judging_body,
        "degree": degree,
        "instance": instance,
        "branch": branch,
        "legal_area": legal_area,
        "authority": authority,
        "collection": collection,
        "document_type": document_type,
        "source_origin": source_origin,
        "access_status": access_status,
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
    if judgment_date_from:
        clauses.append("judgment_date >= ?")
        params.append(_required_storage_date(judgment_date_from))
    if judgment_date_to:
        clauses.append("judgment_date <= ?")
        params.append(_required_storage_date(judgment_date_to))
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


def _enum_value(value: object) -> object:
    """Store string-enum fields as plain values for SQL consumers."""

    return getattr(value, "value", value)


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
        "persisted_record_count": int(row["persisted_record_count"]),
        "label": row["label"],
        "manifest": json.loads(str(row["manifest_json"])) if row["manifest_json"] else None,
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


def _tombstone_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "source": str(row["source"]),
        "canonical_key": str(row["canonical_key"]),
        "evidence_url": str(row["evidence_url"]),
        "evidence_sha256": str(row["evidence_sha256"]),
        "evidence_type": str(row["evidence_type"]),
        "observed_at": str(row["observed_at"]),
        "reason": str(row["reason"]),
        "created_at": str(row["created_at"]),
        "schema_version": "nanojuris-tombstone-evidence-v1",
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
