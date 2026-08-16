"""MCP-ready tool functions for NanoJuris."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

from nanojuris.brazil import CourtBranch, SourceSystem, list_courts
from nanojuris.catalog import get_provider_catalog_entry
from nanojuris.client import NanoJurisClient
from nanojuris.exporters import (
    research_run_to_export,
    search_page_to_markdown,
    to_canonical_jsonl,
    to_csv,
    to_jsonl,
)
from nanojuris.health import check_sources
from nanojuris.source_contracts import summarize_contracts
from nanojuris.store import SQLiteStore, StoredRecordKind
from nanojuris.validation import validate_sources

MAX_MCP_PAGE_SIZE = 100


def list_sources_tool(client: NanoJurisClient | None = None) -> dict[str, Any]:
    """Return declared capabilities for all registered sources."""

    active_client = client or NanoJurisClient()
    return {
        "sources": [
            {
                "capabilities": _to_jsonable(capability),
                "coverage": get_provider_catalog_entry(capability.source),
            }
            for capability in active_client.list_sources()
        ],
    }


def list_courts_tool(
    *,
    branch: CourtBranch | None = None,
    state: str = "",
    source_system: SourceSystem | None = None,
    implemented: bool | None = None,
) -> dict[str, Any]:
    """Return Brazilian judiciary bodies known by NanoJuris."""

    courts = list_courts(
        branch=branch,
        state=state or None,
        source_system=source_system,
        implemented=implemented,
    )
    return {"courts": [court.to_dict() for court in courts]}


def source_diagnostics_tool(
    source: str = "tjdf_juris",
    *,
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Return declared capabilities and limits for one source."""

    active_client = client or NanoJurisClient()
    return {
        "source": source,
        "capabilities": _to_jsonable(active_client.get_capabilities(source=source)),
        "coverage": get_provider_catalog_entry(source),
    }


def source_health_tool(
    *,
    sources: list[str] | None = None,
    text: str = "responsabilidade civil",
    timeout: float | None = None,
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Run an explicit live health check for selected public sources."""

    active_client = client or NanoJurisClient()
    return check_sources(active_client, sources=sources, text=text, timeout=timeout)


def source_validation_tool(
    *,
    sources: list[str] | None = None,
    text: str = "responsabilidade civil",
    timeout: float | None = None,
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Run an explicit live contract validation for selected public sources."""

    active_client = client or NanoJurisClient()
    return validate_sources(active_client, sources=sources, text=text, timeout=timeout)


def source_contracts_tool(
    source: str = "",
    *,
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Return maturity, gaps and recommended deepening steps for provider contracts."""

    active_client = client or NanoJurisClient()
    contracts = (
        [active_client.get_source_contract(source=source)]
        if source
        else active_client.list_source_contracts()
    )
    return {
        "summary": _to_jsonable(summarize_contracts(contracts)),
        "contracts": [_to_jsonable(contract) for contract in contracts],
    }


def list_source_datasets_tool(
    source: str = "stj_dados_abertos_jurisprudencia",
    *,
    query: str = "jurisprudencia",
    rows: int = 20,
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """List public datasets exposed by a provider catalog."""

    active_client = client or NanoJurisClient()
    return {
        "source": source,
        "query": query,
        "rows": rows,
        "datasets": active_client.list_source_datasets(source=source, query=query, rows=rows),
    }


def describe_source_dataset_tool(
    dataset_id: str,
    *,
    source: str = "stj_dados_abertos_jurisprudencia",
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Describe one public dataset and its resources without downloading files."""

    active_client = client or NanoJurisClient()
    return active_client.describe_source_dataset(source=source, dataset_id=dataset_id)


def plan_source_sync_tool(
    dataset_id: str,
    *,
    source: str = "stj_dados_abertos_jurisprudencia",
    format: str = "JSON",
    max_resources: int = 100,
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Plan a bounded dataset sync without performing downloads."""

    active_client = client or NanoJurisClient()
    return active_client.plan_source_sync(
        source=source,
        dataset_id=dataset_id,
        format=format,
        max_resources=max_resources,
    )


def sync_source_resource_tool(
    dataset_id: str,
    resource_id: str,
    db_path: str,
    *,
    source: str = "stj_dados_abertos_jurisprudencia",
    max_bytes: int = 50_000_000,
    label: str | None = None,
    force: bool = False,
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Download one bounded official resource into a local SQLite store."""

    active_client = client or NanoJurisClient()
    with SQLiteStore(db_path) as store:
        result = active_client.sync_source_resource(
            source=source,
            dataset_id=dataset_id,
            resource_id=resource_id,
            store=store,
            max_bytes=max_bytes,
            label=label,
            force=force,
        )
    return {
        "source": source,
        "dataset_id": dataset_id,
        "resource_id": resource_id,
        "db_path": db_path,
        "sync": result,
    }


def search_jurisprudence_tool(
    text: str = "",
    *,
    source: str = "tjdf_juris",
    courts: list[str] | None = None,
    types: list[str] | None = None,
    number: str = "",
    source_origin: str = "",
    date_from: str = "",
    date_to: str = "",
    exact_phrase: str = "",
    rapporteur: str = "",
    page: int = 1,
    page_size: int = 10,
    canonical: bool = True,
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Search a source and return paginated normalized or canonical results."""

    active_client = client or NanoJurisClient()
    normalized_page = _page(page)
    limited_page_size = _limit_page_size(page_size)
    if source.strip().lower() in {"all", "*", "unified"}:
        return _to_jsonable(
            active_client.search_many(
                text,
                courts=courts or [],
                types=types or [],
                number=number,
                source_origin=source_origin,
                published_from=date_from,
                published_to=date_to,
                exact_phrase=exact_phrase,
                rapporteur=rapporteur,
                page=normalized_page,
                page_size=limited_page_size,
                canonical=canonical,
            )
        )
    if canonical:
        records = active_client.search_canonical(
            text,
            source=source,
            courts=courts or [],
            types=types or [],
            number=number,
            source_origin=source_origin,
            published_from=date_from,
            published_to=date_to,
            exact_phrase=exact_phrase,
            rapporteur=rapporteur,
            page=normalized_page,
            page_size=limited_page_size,
        )
        return {
            "source": source,
            "page": normalized_page,
            "page_size": limited_page_size,
            "canonical": True,
            "results": [_to_jsonable(record) for record in records],
        }
    search_page = active_client.search(
        text,
        source=source,
        courts=courts or [],
        types=types or [],
        number=number,
        source_origin=source_origin,
        published_from=date_from,
        published_to=date_to,
        exact_phrase=exact_phrase,
        rapporteur=rapporteur,
        page=normalized_page,
        page_size=limited_page_size,
    )
    return _to_jsonable(search_page)


def search_unified_tool(
    text: str = "",
    *,
    sources: list[str] | None = None,
    courts: list[str] | None = None,
    types: list[str] | None = None,
    number: str = "",
    source_origin: str = "",
    date_from: str = "",
    date_to: str = "",
    exact_phrase: str = "",
    rapporteur: str = "",
    page: int = 1,
    page_size: int = 10,
    canonical: bool = True,
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Search multiple jurisprudence sources and return one unified result list."""

    active_client = client or NanoJurisClient()
    return _to_jsonable(
        active_client.search_many(
            text,
            sources=sources,
            courts=courts or [],
            types=types or [],
            number=number,
            source_origin=source_origin,
            published_from=date_from,
            published_to=date_to,
            exact_phrase=exact_phrase,
            rapporteur=rapporteur,
            page=_page(page),
            page_size=_limit_page_size(page_size),
            canonical=canonical,
        )
    )


def search_unified_store_tool(
    text: str = "",
    *,
    db_path: str,
    sources: list[str] | None = None,
    courts: list[str] | None = None,
    types: list[str] | None = None,
    number: str = "",
    source_origin: str = "",
    page: int = 1,
    page_size: int = 10,
    label: str | None = None,
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Search public sources and save one auditable federated research run."""

    active_client = client or NanoJurisClient()
    run = active_client.search_many_and_store_run(
        text,
        store=db_path,
        sources=sources,
        courts=courts,
        types=types,
        number=number,
        source_origin=source_origin,
        page=_page(page),
        page_size=_limit_page_size(page_size),
        label=label,
    )
    return {"run": run.to_dict()}


def export_results_tool(
    text: str = "",
    *,
    source: str = "tjdf_juris",
    output_format: str = "canonical-jsonl",
    courts: list[str] | None = None,
    types: list[str] | None = None,
    number: str = "",
    page: int = 1,
    page_size: int = 10,
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Search a source and export results in a supported textual format."""

    active_client = client or NanoJurisClient()
    search_page = active_client.search(
        text,
        source=source,
        courts=courts or [],
        types=types or [],
        number=number,
        page=_page(page),
        page_size=_limit_page_size(page_size),
    )
    content = _format_search_page(search_page, output_format)
    return {
        "source": source,
        "format": output_format,
        "content": content,
    }


def get_document_tool(
    document_id: str,
    *,
    source: str = "tjdf_juris",
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Return one public full-text document as a canonical document."""

    active_client = client or NanoJurisClient()
    document = active_client.get_document(document_id, source=source)
    return {
        "source": source,
        "document_id": document_id,
        "document": _to_jsonable(document),
    }


def get_decisions_tool(
    precedent_id: str,
    *,
    source: str = "tjdf_juris",
    client: NanoJurisClient | None = None,
) -> dict[str, Any]:
    """Return public decision texts linked to a provider identifier."""

    active_client = client or NanoJurisClient()
    bundle = active_client.get_decisions(precedent_id, source=source)
    return {
        "source": source,
        "precedent_id": precedent_id,
        "bundle": _to_jsonable(bundle),
    }


def store_stats_tool(db_path: str) -> dict[str, Any]:
    """Return aggregate statistics from a local SQLite canonical store."""

    with SQLiteStore(db_path) as store:
        return store.stats().to_dict()


def store_sync_manifests_tool(
    db_path: str,
    *,
    source: str = "",
    limit: int = 50,
) -> dict[str, Any]:
    """List incremental synchronization manifests from a local store."""

    with SQLiteStore(db_path) as store:
        manifests = store.list_sync_manifests(
            source=source or None,
            limit=_limit_page_size(limit),
        )
    return {
        "db_path": db_path,
        "source": source,
        "limit": _limit_page_size(limit),
        "manifests": manifests,
    }


def store_query_tool(
    db_path: str,
    *,
    kind: StoredRecordKind | None = None,
    source: str = "",
    court: str = "",
    case_number: str = "",
    subject: str = "",
    rapporteur: str = "",
    decision_type: str = "",
    precedent_type: str = "",
    canonical_key: str = "",
    publication_date_from: str = "",
    publication_date_to: str = "",
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """Query a bounded page and expose total/has_more for complete traversal."""

    with SQLiteStore(db_path) as store:
        normalized_limit = _limit_page_size(limit)
        normalized_offset = _offset(offset)
        records = store.query_records(
            kind=kind,
            source=source or None,
            court=court or None,
            case_number=case_number or None,
            subject=subject or None,
            rapporteur=rapporteur or None,
            decision_type=decision_type or None,
            precedent_type=precedent_type or None,
            canonical_key=canonical_key or None,
            publication_date_from=publication_date_from or None,
            publication_date_to=publication_date_to or None,
            limit=normalized_limit,
            offset=normalized_offset,
        )
        total = store.count_records(
            kind=kind,
            source=source or None,
            court=court or None,
            case_number=case_number or None,
            subject=subject or None,
            rapporteur=rapporteur or None,
            decision_type=decision_type or None,
            precedent_type=precedent_type or None,
            canonical_key=canonical_key or None,
            publication_date_from=publication_date_from or None,
            publication_date_to=publication_date_to or None,
        )
    return {
        "db_path": db_path,
        "limit": normalized_limit,
        "offset": normalized_offset,
        "total": total,
        "has_more": normalized_offset + len(records) < total,
        "next_offset": normalized_offset + len(records)
        if normalized_offset + len(records) < total
        else None,
        "results": records,
    }


def store_get_tool(db_path: str, kind: StoredRecordKind, record_id: str) -> dict[str, Any]:
    """Return one canonical record from a local SQLite canonical store."""

    with SQLiteStore(db_path) as store:
        record = store.get(kind, record_id)
    if record is None:
        return {
            "db_path": db_path,
            "kind": kind,
            "id": record_id,
            "found": False,
            "record": None,
        }
    return {
        "db_path": db_path,
        "kind": kind,
        "id": record_id,
        "found": True,
        "record": record,
    }


def store_runs_tool(db_path: str, *, limit: int = 50) -> dict[str, Any]:
    """List saved research runs from a local SQLite canonical store."""

    with SQLiteStore(db_path) as store:
        runs = store.list_research_runs(limit=_limit_page_size(limit))
    return {
        "db_path": db_path,
        "limit": _limit_page_size(limit),
        "runs": runs,
    }


def store_run_tool(db_path: str, run_id: str) -> dict[str, Any]:
    """Return one saved research run from a local SQLite canonical store."""

    with SQLiteStore(db_path) as store:
        run = store.get_research_run(run_id)
    if run is None:
        return {"db_path": db_path, "run_id": run_id, "found": False, "run": None}
    return {
        "db_path": db_path,
        "found": True,
        "run": run,
    }


def store_run_records_tool(
    db_path: str,
    run_id: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """Return canonical records linked to a saved research run."""

    limited = _limit_page_size(limit)
    normalized_offset = _offset(offset)
    with SQLiteStore(db_path) as store:
        records = store.get_research_run_records(
            run_id,
            limit=limited,
            offset=normalized_offset,
        )
        total = store.count_research_run_records(run_id)
    return {
        "db_path": db_path,
        "run_id": run_id,
        "limit": limited,
        "offset": normalized_offset,
        "total": total,
        "has_more": normalized_offset + len(records) < total,
        "next_offset": normalized_offset + len(records)
        if normalized_offset + len(records) < total
        else None,
        "results": records,
    }


def store_export_run_tool(
    db_path: str,
    run_id: str,
    *,
    output_format: str = "jsonl",
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """Export records linked to a saved research run."""

    limited = _limit_page_size(limit)
    normalized_offset = _offset(offset)
    with SQLiteStore(db_path) as store:
        run = store.get_research_run(run_id)
        if run is None:
            raise ValueError("Research run not found")
        records = store.get_research_run_records(
            run_id,
            limit=limited,
            offset=normalized_offset,
        )
        total = store.count_research_run_records(run_id)
    return {
        "db_path": db_path,
        "run_id": run_id,
        "format": output_format,
        "limit": limited,
        "offset": normalized_offset,
        "total": total,
        "has_more": normalized_offset + len(records) < total,
        "next_offset": normalized_offset + len(records)
        if normalized_offset + len(records) < total
        else None,
        "content": research_run_to_export(run, records, output_format),
    }


def _format_search_page(search_page: Any, output_format: str) -> str:
    normalized = output_format.strip().lower()
    if normalized == "json":
        return json.dumps(_to_jsonable(search_page), ensure_ascii=False, indent=2, sort_keys=True)
    if normalized == "jsonl":
        return to_jsonl(search_page)
    if normalized == "canonical-jsonl":
        return to_canonical_jsonl(search_page)
    if normalized == "csv":
        return to_csv(search_page)
    if normalized == "markdown":
        return search_page_to_markdown(search_page)
    raise ValueError(
        "Unsupported export format. Use: json, jsonl, canonical-jsonl, csv or markdown."
    )


def _limit_page_size(page_size: int) -> int:
    return max(1, min(page_size, MAX_MCP_PAGE_SIZE))


def _page(page: int) -> int:
    return max(1, page)


def _offset(offset: int) -> int:
    return max(0, offset)


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
