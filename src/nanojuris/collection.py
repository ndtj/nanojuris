"""Resumable, bounded collection runner for jurisprudence providers."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, TypeAlias
from uuid import uuid4

from nanojuris.canonical import search_page_to_canonical
from nanojuris.errors import safe_error_message
from nanojuris.identity import identity_key
from nanojuris.models import (
    CanonicalDecision,
    CanonicalDocument,
    CanonicalPrecedent,
    JurisprudenceQuery,
    utc_now_iso,
)
from nanojuris.pagination import authoritative_total_reached
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.store import CanonicalStore

CanonicalRecord: TypeAlias = CanonicalDecision | CanonicalDocument | CanonicalPrecedent
CHECKPOINT_SCHEMA_VERSION = 2
CHECKPOINT_FORMAT = "nanojuris-collection-checkpoint-v2"


@dataclass(slots=True)
class CollectionFailure:
    page: int
    error_type: str
    message: str
    record_index: int | None = None
    record_identity: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CollectionFreshness:
    """Freshness evidence for one collection, never a global cache value."""

    observed_at: str
    source_updated_at: str | None = None
    coverage_end_known: bool = False
    evidence_expires_at: str | None = None

    def __post_init__(self) -> None:
        if not self.observed_at.strip():
            raise ValueError("observed_at deve ser informado")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CollectionManifest:
    """Versioned, raw-free manifest describing one bounded collection run."""

    run_id: str
    source: str
    query: dict[str, Any]
    query_fingerprint: str
    contract_fingerprint: str
    started_at: str
    finished_at: str
    outcome: str
    complete: bool
    stop_reason: str
    max_pages: int
    max_records: int
    pages_fetched: int
    records_seen: int
    records_saved: int
    duplicate_records: int
    invalid_records: int
    failures: list[dict[str, Any]] = field(default_factory=list)
    freshness: CollectionFreshness | None = None
    schema_version: str = "nanojuris-collection-manifest-v1"
    last_page: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.run_id.strip() or not self.source.strip():
            raise ValueError("manifest exige run_id e source")
        if self.outcome not in {"complete", "paused", "failed"}:
            raise ValueError("manifest outcome inválido")
        if self.complete != (self.outcome == "complete"):
            raise ValueError("manifest complete/outcome inconsistente")

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


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
    invalid_records: int = 0
    last_error: dict[str, Any] | None = None
    run_id: str = ""
    query_fingerprint: str = ""
    contract_fingerprint: str = ""
    page_fingerprints: list[str] = field(default_factory=list)
    attempts: int = 0
    outcome: str = "running"
    started_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    last_page: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_path(cls, path: str | Path) -> CollectionCheckpoint:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        version = int(payload.get("schema_version", 0))
        if version not in {1, CHECKPOINT_SCHEMA_VERSION}:
            raise ValueError("checkpoint de coleta incompatível")
        return cls(
            schema_version=version,
            source=str(payload["source"]),
            query=dict(payload["query"]),
            next_page=int(payload["next_page"]),
            seen_ids=[str(item) for item in payload.get("seen_ids", [])],
            pages_fetched=int(payload.get("pages_fetched", 0)),
            records_seen=int(payload.get("records_seen", 0)),
            records_saved=int(payload.get("records_saved", 0)),
            duplicate_records=int(payload.get("duplicate_records", 0)),
            invalid_records=int(payload.get("invalid_records", 0)),
            last_error=payload.get("last_error"),
            run_id=str(payload.get("run_id", "")),
            query_fingerprint=str(payload.get("query_fingerprint", "")),
            contract_fingerprint=str(payload.get("contract_fingerprint", "")),
            page_fingerprints=[str(item) for item in payload.get("page_fingerprints", [])],
            attempts=int(payload.get("attempts", 0)),
            outcome=str(payload.get("outcome", "running")),
            started_at=str(payload.get("started_at") or payload.get("updated_at") or utc_now_iso()),
            updated_at=str(payload.get("updated_at") or utc_now_iso()),
            last_page=dict(payload["last_page"])
            if isinstance(payload.get("last_page"), dict)
            else None,
        )

    def write_atomic(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        payload = (
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, "wb") as stream:
                fd = -1
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(target)
        finally:
            if fd != -1:
                os.close(fd)
            temporary.unlink(missing_ok=True)


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
    run_id: str | None = None
    query_fingerprint: str | None = None
    contract_fingerprint: str | None = None
    freshness: CollectionFreshness | None = None
    manifest: CollectionManifest | None = None
    last_page: dict[str, Any] | None = None

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
            "run_id": self.run_id,
            "query_fingerprint": self.query_fingerprint,
            "contract_fingerprint": self.contract_fingerprint,
            "freshness": self.freshness.to_dict() if self.freshness is not None else None,
            "manifest": self.manifest.to_dict() if self.manifest is not None else None,
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
        started_at = utc_now_iso()
        query_fingerprint = _query_fingerprint(query_payload)
        contract_fingerprint = _provider_contract_fingerprint(self.provider)
        checkpoint = self._load_checkpoint(query_payload, source) if resume else None
        last_page: dict[str, Any] | None = None
        if checkpoint is None:
            run_id = f"collection-{uuid4().hex}"
            next_page = query.page
            seen_ids: set[str] = set()
            page_fingerprints: list[str] = []
            pages_fetched = records_seen = records_saved = duplicate_records = 0
            invalid_records = 0
            attempts = 0
        else:
            run_id = checkpoint.run_id or f"collection-{uuid4().hex}"
            started_at = checkpoint.started_at
            next_page = checkpoint.next_page
            seen_ids = set(checkpoint.seen_ids)
            page_fingerprints = list(checkpoint.page_fingerprints)
            pages_fetched = checkpoint.pages_fetched
            records_seen = checkpoint.records_seen
            records_saved = checkpoint.records_saved
            duplicate_records = checkpoint.duplicate_records
            invalid_records = checkpoint.invalid_records
            attempts = checkpoint.attempts
            last_page = checkpoint.last_page

        records: list[CanonicalRecord] = []
        failures: list[CollectionFailure] = []
        complete = False
        stop_reason = "max_pages"
        pages_this_run = 0
        inconsistent_total = False
        while pages_this_run < self.max_pages and len(records) < self.max_records:
            current_query = replace(query, page=next_page)
            attempts += 1
            try:
                page = self.provider.search(current_query)
            except Exception as exc:  # provider errors become an auditable manifest
                failure = CollectionFailure(
                    next_page,
                    type(exc).__name__,
                    safe_error_message(exc),
                )
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
                    invalid_records=invalid_records,
                    last_error=failure.to_dict(),
                    run_id=run_id,
                    query_fingerprint=query_fingerprint,
                    contract_fingerprint=contract_fingerprint,
                    page_fingerprints=page_fingerprints,
                    attempts=attempts,
                    outcome="failed",
                    started_at=started_at,
                    last_page=last_page,
                )
                stop_reason = "provider_error"
                break

            pages_this_run += 1
            pages_fetched += 1
            last_page = _page_observability(page)
            try:
                page_results = list(page.results)
            except Exception as exc:
                failure = CollectionFailure(
                    next_page,
                    type(exc).__name__,
                    safe_error_message(exc),
                )
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
                    invalid_records=invalid_records,
                    last_error=failure.to_dict(),
                    run_id=run_id,
                    query_fingerprint=query_fingerprint,
                    contract_fingerprint=contract_fingerprint,
                    page_fingerprints=page_fingerprints,
                    attempts=attempts,
                    outcome="failed",
                    started_at=started_at,
                    last_page=last_page,
                )
                stop_reason = "invalid_page"
                break
            page_fingerprints.append(_page_fingerprint(replace(page, results=page_results)))
            records_seen += len(page_results)
            invalid_records_at_page_start = invalid_records
            unique_results: list[
                tuple[int, Any, str, list[CanonicalDecision | CanonicalPrecedent]]
            ] = []
            page_identities: set[str] = set()
            for record_index, result in enumerate(page_results):
                try:
                    identity = _result_identity(result)
                    canonical = search_page_to_canonical(replace(page, results=[result]))
                    if not canonical:
                        raise ValueError("canonicalização não produziu registro")
                except Exception as exc:
                    invalid_records += 1
                    failures.append(
                        CollectionFailure(
                            next_page,
                            type(exc).__name__,
                            safe_error_message(exc),
                            record_index=record_index,
                            record_identity=_safe_result_identity(result),
                        )
                    )
                    continue
                if identity in seen_ids or identity in page_identities:
                    duplicate_records += 1
                    continue
                page_identities.add(identity)
                unique_results.append((record_index, result, identity, canonical))

            remaining = self.max_records - len(records)
            limited_by_record_cap = len(unique_results) > remaining
            if len(unique_results) > remaining:
                unique_results = unique_results[:remaining]
            canonical_records: list[CanonicalRecord] = []
            accepted_results: list[Any] = []
            for _record_index, result, _identity, canonical in unique_results:
                canonical_records.extend(canonical)
                accepted_results.append(result)

            seen_ids.update(_result_identity(result) for result in accepted_results)
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
                invalid_records=invalid_records,
                run_id=run_id,
                query_fingerprint=query_fingerprint,
                contract_fingerprint=contract_fingerprint,
                page_fingerprints=page_fingerprints,
                attempts=attempts,
                outcome="running",
                started_at=started_at,
                last_page=last_page,
            )

            if not page_results:
                # If a previous page declared total=0 while returning rows,
                # the following empty page cannot repair that contradiction.
                # Preserve the conservative incomplete state instead of
                # reporting a complete collection.
                complete = not inconsistent_total
                stop_reason = "no_results" if complete else "inconsistent_total"
                break
            if limited_by_record_cap:
                stop_reason = "max_records"
                break
            if (
                page_results
                and not accepted_results
                and invalid_records > invalid_records_at_page_start
            ):
                complete = False
                stop_reason = "invalid_records"
                break
            if page.is_complete is True or (
                authoritative_total_reached(
                    reported_total=page.total,
                    total_known=page.total_known,
                    returned=len(page_results),
                    accumulated=len(seen_ids),
                )
            ):
                complete = True
                stop_reason = page.completeness_reason or "provider_complete"
                break
            if (
                page.total_known is True
                and page.total == 0
                and page_results
                and page.is_complete is not True
            ):
                # A known zero with rows is an upstream contract violation. Do
                # not keep paging and later mistake an empty follow-up page for
                # proof that the first page was complete.
                inconsistent_total = True
                complete = False
                stop_reason = "inconsistent_total"
                break
            if page_results and not unique_results:
                complete = False
                stop_reason = (
                    "invalid_records"
                    if invalid_records > invalid_records_at_page_start
                    else "repeated_page"
                )
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
        final_outcome = "complete" if complete else ("failed" if failures else "paused")
        freshness = CollectionFreshness(observed_at=utc_now_iso())
        manifest = CollectionManifest(
            run_id=run_id,
            source=source,
            query=_redact_query(query_payload),
            query_fingerprint=query_fingerprint,
            contract_fingerprint=contract_fingerprint,
            started_at=started_at,
            finished_at=freshness.observed_at,
            outcome=final_outcome,
            complete=complete,
            stop_reason=stop_reason,
            max_pages=self.max_pages,
            max_records=self.max_records,
            pages_fetched=pages_fetched,
            records_seen=records_seen,
            records_saved=records_saved,
            duplicate_records=duplicate_records,
            invalid_records=invalid_records,
            failures=[failure.to_dict() for failure in failures],
            freshness=freshness,
            last_page=last_page,
        )
        if self.checkpoint_path is not None and not (complete and clear_checkpoint_on_complete):
            self._checkpoint(
                source=source,
                query=query_payload,
                next_page=next_page,
                seen_ids=seen_ids,
                pages_fetched=pages_fetched,
                records_seen=records_seen,
                records_saved=records_saved,
                duplicate_records=duplicate_records,
                invalid_records=invalid_records,
                last_error=failures[-1].to_dict() if failures else None,
                run_id=run_id,
                query_fingerprint=query_fingerprint,
                contract_fingerprint=contract_fingerprint,
                page_fingerprints=page_fingerprints,
                attempts=attempts,
                outcome=final_outcome,
                started_at=started_at,
                last_page=last_page,
            )
        if complete and clear_checkpoint_on_complete and self.checkpoint_path is not None:
            self.checkpoint_path.unlink(missing_ok=True)
        return CollectionReport(
            source=source,
            pages_fetched=pages_fetched,
            records_seen=records_seen,
            records_saved=records_saved,
            duplicate_records=duplicate_records,
            invalid_records=invalid_records,
            next_page=next_page,
            complete=complete,
            stop_reason=stop_reason,
            failures=failures,
            records=records,
            checkpoint_path=str(self.checkpoint_path) if self.checkpoint_path else None,
            run_id=run_id,
            query_fingerprint=query_fingerprint,
            contract_fingerprint=contract_fingerprint,
            freshness=freshness,
            manifest=manifest,
            last_page=last_page,
        )

    def _load_checkpoint(
        self,
        query_payload: dict[str, Any],
        source: str,
    ) -> CollectionCheckpoint | None:
        if self.checkpoint_path is None or not self.checkpoint_path.exists():
            return None
        checkpoint = CollectionCheckpoint.from_path(self.checkpoint_path)
        if checkpoint.schema_version != CHECKPOINT_SCHEMA_VERSION:
            raise ValueError(
                "checkpoint legado sem fingerprint de contrato; "
                "execute com resume=False para reiniciar"
            )
        if checkpoint.source != source:
            raise ValueError("checkpoint pertence a outro provider")
        if checkpoint.query_fingerprint != _query_fingerprint(query_payload):
            raise ValueError("checkpoint pertence a outra impressão digital de consulta")
        if checkpoint.contract_fingerprint != _provider_contract_fingerprint(self.provider):
            raise ValueError("checkpoint incompatível com o contrato atual do provider")
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
        invalid_records: int,
        last_error: dict[str, Any] | None = None,
        run_id: str = "",
        query_fingerprint: str = "",
        contract_fingerprint: str = "",
        page_fingerprints: list[str] | None = None,
        attempts: int = 0,
        outcome: str = "running",
        started_at: str | None = None,
        last_page: dict[str, Any] | None = None,
    ) -> None:
        if self.checkpoint_path is None:
            return
        CollectionCheckpoint(
            schema_version=CHECKPOINT_SCHEMA_VERSION,
            source=source,
            query=_redact_query(query),
            next_page=next_page,
            seen_ids=sorted(seen_ids),
            pages_fetched=pages_fetched,
            records_seen=records_seen,
            records_saved=records_saved,
            duplicate_records=duplicate_records,
            invalid_records=invalid_records,
            last_error=last_error,
            run_id=run_id,
            query_fingerprint=query_fingerprint,
            contract_fingerprint=contract_fingerprint,
            page_fingerprints=list(page_fingerprints or []),
            attempts=attempts,
            outcome=outcome,
            started_at=started_at or utc_now_iso(),
            updated_at=utc_now_iso(),
            last_page=last_page,
        ).write_atomic(self.checkpoint_path)


def _query_fingerprint(query: dict[str, Any]) -> str:
    """Hash query intent while ignoring the mutable page cursor."""

    payload = {key: value for key, value in query.items() if key != "page"}
    return _stable_fingerprint(payload)


def _redact_query(query: dict[str, Any]) -> dict[str, Any]:
    """Keep checkpoint/manifest queries useful without persisting PII fields."""

    sensitive_fields = {
        "party_document",
        "party_name",
        "police_document",
        "lawyer_name",
        "oab",
    }
    return {
        key: ("<redacted>" if key in sensitive_fields and value else value)
        for key, value in query.items()
    }


def _provider_contract_fingerprint(provider: JurisprudenceProvider) -> str:
    """Hash the provider contract used by a resumable collection."""

    capabilities = provider.get_capabilities()
    payload = {
        "format": CHECKPOINT_FORMAT,
        "provider": provider.name,
        "provider_class": f"{provider.__class__.__module__}.{provider.__class__.__qualname__}",
        "capabilities": _json_safe(capabilities.to_dict()),
        "parameters": _json_safe(
            provider.get_parameters() if hasattr(provider, "get_parameters") else {}
        ),
    }
    return _stable_fingerprint(payload)


def _page_fingerprint(page: Any) -> str:
    """Hash page shape and result identities without persisting raw content."""

    payload = {
        "source": page.source,
        "total": page.total,
        "total_known": page.total_known,
        "start": page.start,
        "end": page.end,
        "page": page.page,
        "page_size": page.page_size,
        "pagination_mode": page.pagination_mode,
        "cursor": page.cursor,
        "ordering": page.ordering,
        "is_complete": page.is_complete,
        "access_status": getattr(page.access_status, "value", page.access_status),
        "extraction_status": getattr(page.extraction_status, "value", page.extraction_status),
        "result_identities": [_result_identity(result) for result in page.results],
    }
    return _stable_fingerprint(payload)


def _page_observability(page: Any) -> dict[str, Any]:
    """Return bounded page telemetry suitable for a checkpoint or manifest."""

    trace = getattr(page, "source_trace", None)
    return {
        "source": str(getattr(page, "source", "")),
        "page": int(getattr(page, "page", 0)),
        "total": int(getattr(page, "total", 0)),
        "total_known": getattr(page, "total_known", None),
        "returned": len(getattr(page, "results", []) or []),
        "is_complete": getattr(page, "is_complete", None),
        "access_status": _enum_value(getattr(page, "access_status", None)),
        "extraction_status": _enum_value(getattr(page, "extraction_status", None)),
        "retrieval_status": getattr(trace, "retrieval_status", None),
        "http_status": getattr(trace, "http_status", None),
        "response_bytes": getattr(trace, "response_bytes", None),
        "content_sha256": getattr(trace, "content_sha256", None),
    }


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _stable_fingerprint(value: Any) -> str:
    material = json.dumps(
        _json_safe(value), ensure_ascii=False, sort_keys=True, default=str
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _result_identity(result: Any) -> str:
    semantic_fields = {
        name: getattr(result, name, None)
        for name in (
            "question",
            "thesis",
            "summary",
            "rapporteur",
            "judgment_date",
            "publication_date",
            "updated_at",
            "status",
        )
    }
    return identity_key(
        source=getattr(result, "source", ""),
        court=getattr(result, "court", ""),
        identifier=getattr(result, "id", ""),
        number=getattr(result, "number", ""),
        record_type=getattr(result, "type", ""),
        semantic_fields=semantic_fields,
    )


def _safe_result_identity(result: Any) -> str | None:
    try:
        return _result_identity(result)
    except Exception:
        return None


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
    "CHECKPOINT_FORMAT",
    "CHECKPOINT_SCHEMA_VERSION",
    "CollectionCheckpoint",
    "CollectionFailure",
    "CollectionFreshness",
    "CollectionManifest",
    "CollectionReport",
    "CollectionRunner",
]
