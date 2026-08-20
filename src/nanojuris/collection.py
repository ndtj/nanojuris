"""Resumable, bounded collection runner for jurisprudence providers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from nanojuris.canonical import search_page_to_canonical
from nanojuris.models import (
    CanonicalDecision,
    CanonicalDocument,
    CanonicalPrecedent,
    JurisprudenceQuery,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.store import CanonicalStore

CanonicalRecord = CanonicalDecision | CanonicalDocument | CanonicalPrecedent


@dataclass(slots=True)
class CollectionFailure:
    page: int
    error_type: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CollectionCheckpoint:
    """JSON-serializable state for one provider collection."""

    schema_version: int
    source: str
    query: dict[str, Any]
    next_page: int
    seen_ids: list[str] = field(default_factory=list)
    pages_fetched: int = 0
    records_seen: int = 0
    records_saved: int = 0
    duplicate_records: int = 0
    last_error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_path(cls, path: str | Path) -> CollectionCheckpoint:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if int(payload.get("schema_version", 0)) != 1:
            raise ValueError("checkpoint de coleta incompatível")
        return cls(
            schema_version=1,
            source=str(payload["source"]),
            query=dict(payload["query"]),
            next_page=int(payload["next_page"]),
            seen_ids=[str(item) for item in payload.get("seen_ids", [])],
            pages_fetched=int(payload.get("pages_fetched", 0)),
            records_seen=int(payload.get("records_seen", 0)),
            records_saved=int(payload.get("records_saved", 0)),
            duplicate_records=int(payload.get("duplicate_records", 0)),
            last_error=payload.get("last_error"),
        )

    def write_atomic(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)


@dataclass(slots=True)
class CollectionReport:
    source: str
    pages_fetched: int
    records_seen: int
    records_saved: int
    duplicate_records: int
    invalid_records: int
    next_page: int
    complete: bool
    stop_reason: str
    failures: list[CollectionFailure] = field(default_factory=list)
    records: list[CanonicalRecord] = field(default_factory=list, repr=False)
    checkpoint_path: str | None = None

    def to_dict(self, *, include_records: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": self.source,
            "pages_fetched": self.pages_fetched,
            "records_seen": self.records_seen,
            "records_saved": self.records_saved,
            "duplicate_records": self.duplicate_records,
            "invalid_records": self.invalid_records,
            "next_page": self.next_page,
            "complete": self.complete,
            "stop_reason": self.stop_reason,
            "failures": [failure.to_dict() for failure in self.failures],
            "record_count": len(self.records),
            "checkpoint_path": self.checkpoint_path,
        }
        if include_records:
            payload["records"] = [_record_to_dict(record) for record in self.records]
        return payload


class CollectionRunner:
    """Collect pages, canonicalize records and checkpoint progress."""

    def __init__(
        self,
        provider: JurisprudenceProvider,
        *,
        store: CanonicalStore | None = None,
        checkpoint_path: str | Path | None = None,
        max_pages: int = 100,
        max_records: int = 10_000,
    ) -> None:
        if max_pages < 1 or max_records < 1:
            raise ValueError("max_pages e max_records devem ser positivos")
        self.provider = provider
        self.store = store
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path is not None else None
        self.max_pages = max_pages
        self.max_records = max_records

    def collect(
        self,
        query: JurisprudenceQuery,
        *,
        resume: bool = True,
        clear_checkpoint_on_complete: bool = False,
    ) -> CollectionReport:
        """Collect one provider without exceeding page or record limits."""

        source = self.provider.name
        query_payload = asdict(query)
        checkpoint = self._load_checkpoint(query_payload, source) if resume else None
        if checkpoint is None:
            next_page = query.page
            seen_ids: set[str] = set()
            pages_fetched = records_seen = records_saved = duplicate_records = 0
        else:
            next_page = checkpoint.next_page
            seen_ids = set(checkpoint.seen_ids)
            pages_fetched = checkpoint.pages_fetched
            records_seen = checkpoint.records_seen
            records_saved = checkpoint.records_saved
            duplicate_records = checkpoint.duplicate_records

        records: list[CanonicalRecord] = []
        failures: list[CollectionFailure] = []
        complete = False
        stop_reason = "max_pages"
        pages_this_run = 0
        while pages_this_run < self.max_pages and len(records) < self.max_records:
            current_query = replace(query, page=next_page)
            try:
                page = self.provider.search(current_query)
            except Exception as exc:  # provider errors become an auditable manifest
                failure = CollectionFailure(next_page, type(exc).__name__, str(exc))
                failures.append(failure)
                self._checkpoint(
                    source=source,
                    query=query_payload,
                    next_page=next_page,
                    seen_ids=seen_ids,
                    pages_fetched=pages_fetched,
                    records_seen=records_seen,
                    records_saved=records_saved,
                    duplicate_records=duplicate_records,
                    last_error=failure.to_dict(),
                )
                stop_reason = "provider_error"
                break

            pages_this_run += 1
            pages_fetched += 1
            records_seen += len(page.results)
            unique_results = []
            page_identities: set[str] = set()
            for result in page.results:
                identity = _result_identity(result)
                if identity in seen_ids or identity in page_identities:
                    duplicate_records += 1
                    continue
                page_identities.add(identity)
                unique_results.append(result)

            remaining = self.max_records - len(records)
            limited_by_record_cap = len(unique_results) > remaining
            if len(unique_results) > remaining:
                unique_results = unique_results[:remaining]
            page_for_canonical = replace(page, results=unique_results)
            try:
                canonical_records = search_page_to_canonical(page_for_canonical)
            except Exception as exc:
                failure = CollectionFailure(next_page, type(exc).__name__, str(exc))
                failures.append(failure)
                self._checkpoint(
                    source=source,
                    query=query_payload,
                    next_page=next_page,
                    seen_ids=seen_ids,
                    pages_fetched=pages_fetched,
                    records_seen=records_seen,
                    records_saved=records_saved,
                    duplicate_records=duplicate_records,
                    last_error=failure.to_dict(),
                )
                stop_reason = "canonicalization_error"
                break

            seen_ids.update(_result_identity(result) for result in unique_results)
            if self.store is not None:
                self.store.save_many(canonical_records)
            records.extend(canonical_records)
            records_saved += len(canonical_records)
            if not limited_by_record_cap:
                next_page += 1
            self._checkpoint(
                source=source,
                query=query_payload,
                next_page=next_page,
                seen_ids=seen_ids,
                pages_fetched=pages_fetched,
                records_seen=records_seen,
                records_saved=records_saved,
                duplicate_records=duplicate_records,
            )

            if not page.results:
                complete = True
                stop_reason = "no_results"
                break
            if limited_by_record_cap:
                stop_reason = "max_records"
                break
            if page.is_complete is True or (page.total > 0 and len(seen_ids) >= page.total):
                complete = True
                stop_reason = page.completeness_reason or "provider_complete"
                break
            if page.results and not unique_results:
                complete = False
                stop_reason = "repeated_page"
                break
            if len(records) >= self.max_records:
                stop_reason = "max_records"
                break

        if (
            pages_this_run >= self.max_pages
            and not complete
            and not failures
            and stop_reason not in {"max_records", "repeated_page"}
        ):
            stop_reason = "max_pages"
        if complete and clear_checkpoint_on_complete and self.checkpoint_path is not None:
            self.checkpoint_path.unlink(missing_ok=True)
        return CollectionReport(
            source=source,
            pages_fetched=pages_fetched,
            records_seen=records_seen,
            records_saved=records_saved,
            duplicate_records=duplicate_records,
            invalid_records=0,
            next_page=next_page,
            complete=complete,
            stop_reason=stop_reason,
            failures=failures,
            records=records,
            checkpoint_path=str(self.checkpoint_path) if self.checkpoint_path else None,
        )

    def _load_checkpoint(
        self,
        query_payload: dict[str, Any],
        source: str,
    ) -> CollectionCheckpoint | None:
        if self.checkpoint_path is None or not self.checkpoint_path.exists():
            return None
        checkpoint = CollectionCheckpoint.from_path(self.checkpoint_path)
        if checkpoint.source != source:
            raise ValueError("checkpoint pertence a outro provider")
        expected = dict(query_payload)
        stored = dict(checkpoint.query)
        expected.pop("page", None)
        stored.pop("page", None)
        if expected != stored:
            raise ValueError("checkpoint pertence a outra consulta")
        return checkpoint

    def _checkpoint(
        self,
        *,
        source: str,
        query: dict[str, Any],
        next_page: int,
        seen_ids: set[str],
        pages_fetched: int,
        records_seen: int,
        records_saved: int,
        duplicate_records: int,
        last_error: dict[str, Any] | None = None,
    ) -> None:
        if self.checkpoint_path is None:
            return
        CollectionCheckpoint(
            schema_version=1,
            source=source,
            query=query,
            next_page=next_page,
            seen_ids=sorted(seen_ids),
            pages_fetched=pages_fetched,
            records_seen=records_seen,
            records_saved=records_saved,
            duplicate_records=duplicate_records,
            last_error=last_error,
        ).write_atomic(self.checkpoint_path)


def _result_identity(result: Any) -> str:
    source = str(getattr(result, "source", ""))
    identifier = str(getattr(result, "id", "") or "")
    if identifier:
        return f"{source}:{identifier}"
    number = str(getattr(result, "number", "") or "")
    return f"{source}:{number}:{getattr(result, 'type', '')}"


def _record_to_dict(record: CanonicalRecord) -> dict[str, Any]:
    if hasattr(record, "to_dict"):
        return record.to_dict()  # type: ignore[no-any-return]
    payload = asdict(record)
    return _json_safe(payload)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


__all__ = [
    "CollectionCheckpoint",
    "CollectionFailure",
    "CollectionReport",
    "CollectionRunner",
]
