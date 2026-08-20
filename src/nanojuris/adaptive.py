"""Reviewable memory for structural selector suggestions.

This is deliberately an approval store, not an autonomous parser mutator.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from nanojuris.parsing import HtmlDocument, HtmlNode


@dataclass(frozen=True, slots=True)
class SelectorMemoryEntry:
    id: int
    document_sha256: str
    source: str
    field: str
    selector: str
    matches: int
    confidence: float
    evidence: str
    approved: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SelectorMemory:
    """SQLite-backed selector memory with explicit approval gates."""

    def __init__(self, path: str | Path | sqlite3.Connection):
        self._owns_connection = not isinstance(path, sqlite3.Connection)
        self.connection = path if isinstance(path, sqlite3.Connection) else sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.initialize()

    def initialize(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS selector_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_sha256 TEXT NOT NULL,
                source TEXT NOT NULL,
                field TEXT NOT NULL,
                selector TEXT NOT NULL,
                matches INTEGER NOT NULL,
                confidence REAL NOT NULL,
                evidence TEXT NOT NULL,
                approved INTEGER NOT NULL DEFAULT 0,
                UNIQUE(document_sha256, source, field, selector)
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_selector_memory_lookup "
            "ON selector_memory(source, field, approved)"
        )
        self.connection.commit()

    def remember(
        self,
        document: HtmlDocument,
        *,
        source: str,
        field: str,
        selector: str,
        matches: int,
        confidence: float,
        evidence: str,
        approved: bool = False,
    ) -> SelectorMemoryEntry:
        if not selector.strip():
            raise ValueError("selector não pode ser vazio")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence deve estar entre 0 e 1")
        self.connection.execute(
            """
            INSERT INTO selector_memory (
                document_sha256, source, field, selector, matches,
                confidence, evidence, approved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_sha256, source, field, selector) DO UPDATE SET
                matches=excluded.matches,
                confidence=excluded.confidence,
                evidence=excluded.evidence,
                approved=MAX(selector_memory.approved, excluded.approved)
            """,
            (
                document.sha256,
                source,
                field,
                selector,
                max(0, matches),
                confidence,
                evidence,
                int(approved),
            ),
        )
        self.connection.commit()
        row = self.connection.execute(
            """
            SELECT * FROM selector_memory
            WHERE document_sha256 = ? AND source = ? AND field = ? AND selector = ?
            """,
            (document.sha256, source, field, selector),
        ).fetchone()
        if row is None:  # pragma: no cover - guarded by the insert above
            raise RuntimeError("falha ao persistir memória de seletor")
        return _row_to_entry(row)

    def approve(self, entry_id: int) -> SelectorMemoryEntry:
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE selector_memory SET approved = 1 WHERE id = ?",
                (entry_id,),
            )
        if cursor.rowcount != 1:
            raise KeyError(f"seletor não encontrado: {entry_id}")
        row = self.connection.execute(
            "SELECT * FROM selector_memory WHERE id = ?", (entry_id,)
        ).fetchone()
        if row is None:  # pragma: no cover
            raise KeyError(entry_id)
        return _row_to_entry(row)

    def list_candidates(
        self,
        *,
        source: str,
        field: str,
        approved_only: bool = False,
        limit: int = 20,
    ) -> list[SelectorMemoryEntry]:
        rows = self.connection.execute(
            """
            SELECT * FROM selector_memory
            WHERE source = ? AND field = ? AND (? = 0 OR approved = 1)
            ORDER BY approved DESC, confidence DESC, matches ASC, id ASC
            LIMIT ?
            """,
            (source, field, int(approved_only), max(1, limit)),
        ).fetchall()
        return [_row_to_entry(row) for row in rows]

    def resolve(
        self,
        document: HtmlDocument,
        *,
        source: str,
        field: str,
        limit: int = 20,
    ) -> list[HtmlNode]:
        """Apply only approved selectors that still match the new document."""

        nodes: list[HtmlNode] = []
        for entry in self.list_candidates(
            source=source,
            field=field,
            approved_only=True,
            limit=limit,
        ):
            matches = document.css(entry.selector)
            nodes.extend(matches)
            if nodes:
                break
        return nodes

    def close(self) -> None:
        if self._owns_connection:
            self.connection.close()

    def __enter__(self) -> "SelectorMemory":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _row_to_entry(row: sqlite3.Row) -> SelectorMemoryEntry:
    return SelectorMemoryEntry(
        id=int(row["id"]),
        document_sha256=str(row["document_sha256"]),
        source=str(row["source"]),
        field=str(row["field"]),
        selector=str(row["selector"]),
        matches=int(row["matches"]),
        confidence=float(row["confidence"]),
        evidence=str(row["evidence"]),
        approved=bool(row["approved"]),
    )


__all__ = ["SelectorMemory", "SelectorMemoryEntry"]
