"""Optional MCP server entrypoint for NanoJuris."""

from __future__ import annotations

import os
import re
from importlib import import_module
from pathlib import Path
from typing import Any, cast

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


def create_server() -> Any:
    """Create a FastMCP server when the optional MCP dependency is installed."""

    try:
        fastmcp_module = import_module("mcp.server.fastmcp")
        server_factory = fastmcp_module.FastMCP
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional extra
        if exc.name != "mcp.server.fastmcp":
            raise
        try:
            mcp_module = import_module("mcp.server")
            server_factory = mcp_module.MCPServer
        except (ImportError, AttributeError) as fallback_exc:
            raise RuntimeError(
                "Install NanoJuris with the MCP extra: nanojuris[mcp]"
            ) from fallback_exc
    except (ImportError, AttributeError) as exc:  # pragma: no cover
        raise RuntimeError("Install NanoJuris with the MCP extra: nanojuris[mcp]") from exc

    server = server_factory("nanojuris")

    @server.tool()
    def list_sources() -> dict[str, Any]:
        """List declared NanoJuris sources and extraction capabilities."""

        return list_sources_tool()

    @server.tool()
    def list_courts(
        branch: str | None = None,
        state: str = "",
        source_system: str | None = None,
        implemented: bool | None = None,
    ) -> dict[str, Any]:
        """List Brazilian judiciary bodies known by NanoJuris."""

        allowed = {
            None,
            "constitutional",
            "superior",
            "federal",
            "state",
            "labor",
            "electoral",
            "military",
            "national_council",
        }
        if branch not in allowed:
            raise ValueError("branch must be a known Brazilian judiciary branch")
        return list_courts_tool(
            branch=cast(Any, branch),
            state=state,
            source_system=cast(Any, source_system),
            implemented=implemented,
        )

    @server.tool()
    def source_diagnostics(source: str = "bnp_pangea") -> dict[str, Any]:
        """Return source capabilities, limits and responsible-use notes."""

        return source_diagnostics_tool(source)

    @server.tool()
    def source_contracts(source: str = "") -> dict[str, Any]:
        """Return source contract maturity, gaps and deepening steps."""

        return source_contracts_tool(source)

    @server.tool()
    def search_jurisprudence(
        text: str = "",
        source: str = "bnp_pangea",
        courts: list[str] | None = None,
        types: list[str] | None = None,
        number: str = "",
        source_origin: str = "",
        page: int = 1,
        page_size: int = 10,
        canonical: bool = True,
    ) -> dict[str, Any]:
        """Search public jurisprudence and return normalized/canonical data."""

        return search_jurisprudence_tool(
            text,
            source=source,
            courts=courts,
            types=types,
            number=number,
            source_origin=source_origin,
            page=page,
            page_size=page_size,
            canonical=canonical,
        )

    @server.tool()
    def search_unified(
        text: str = "",
        sources: list[str] | None = None,
        courts: list[str] | None = None,
        types: list[str] | None = None,
        number: str = "",
        source_origin: str = "",
        page: int = 1,
        page_size: int = 10,
        canonical: bool = True,
    ) -> dict[str, Any]:
        """Search multiple public jurisprudence sources in one MCP call."""

        return search_unified_tool(
            text,
            sources=sources,
            courts=courts,
            types=types,
            number=number,
            source_origin=source_origin,
            page=page,
            page_size=page_size,
            canonical=canonical,
        )

    @server.tool()
    def export_results(
        text: str = "",
        source: str = "bnp_pangea",
        output_format: str = "canonical-jsonl",
        courts: list[str] | None = None,
        types: list[str] | None = None,
        number: str = "",
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """Search and export public jurisprudence results."""

        return export_results_tool(
            text,
            source=source,
            output_format=output_format,
            courts=courts,
            types=types,
            number=number,
            page=page,
            page_size=page_size,
        )

    @server.tool()
    def get_document(document_id: str, source: str = "tjsp_cjsg") -> dict[str, Any]:
        """Return one public full-text document as canonical extraction data."""

        return get_document_tool(document_id, source=source)

    @server.tool()
    def get_decisions(precedent_id: str, source: str = "bnp_pangea") -> dict[str, Any]:
        """Return public decision texts linked to a provider identifier."""

        return get_decisions_tool(precedent_id, source=source)

    @server.tool()
    def store_stats(store_id: str = "default") -> dict[str, Any]:
        """Return aggregate statistics from a local NanoJuris SQLite store."""

        return store_stats_tool(str(_resolve_store_id(store_id)))

    @server.tool()
    def store_query(
        store_id: str = "default",
        kind: str | None = None,
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
    ) -> dict[str, Any]:
        """Query records from a local NanoJuris SQLite store."""

        if kind not in {None, "decision", "document", "precedent"}:
            raise ValueError("kind must be decision, document or precedent")
        return store_query_tool(
            str(_resolve_store_id(store_id)),
            kind=cast(Any, kind),
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
            limit=limit,
        )

    @server.tool()
    def store_get(store_id: str, kind: str, record_id: str) -> dict[str, Any]:
        """Return one canonical record from a local NanoJuris SQLite store."""

        if kind not in {"decision", "document", "precedent"}:
            raise ValueError("kind must be decision, document or precedent")
        return store_get_tool(str(_resolve_store_id(store_id)), cast(Any, kind), record_id)

    @server.tool()
    def store_runs(store_id: str = "default", limit: int = 50) -> dict[str, Any]:
        """List saved research runs from a local NanoJuris SQLite store."""

        return store_runs_tool(str(_resolve_store_id(store_id)), limit=limit)

    @server.tool()
    def store_run(store_id: str, run_id: str) -> dict[str, Any]:
        """Return one saved research run from a local NanoJuris SQLite store."""

        return store_run_tool(str(_resolve_store_id(store_id)), run_id)

    @server.tool()
    def store_run_records(
        store_id: str,
        run_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Return records linked to a saved research run."""

        return store_run_records_tool(
            str(_resolve_store_id(store_id)), run_id, limit=limit, offset=offset
        )

    @server.tool()
    def store_export_run(
        store_id: str,
        run_id: str,
        output_format: str = "jsonl",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Export records linked to a saved research run."""

        return store_export_run_tool(
            str(_resolve_store_id(store_id)),
            run_id,
            output_format=output_format,
            limit=limit,
            offset=offset,
        )

    return server


def _resolve_store_id(store_id: str) -> Path:
    """Resolve an MCP store identifier below the configured local store root."""

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", store_id):
        raise ValueError("store_id must be a simple local identifier, not a filesystem path")
    root = Path(os.getenv("NANOJURIS_STORE_ROOT", "~/.nanojuris/stores")).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    candidate = (root / f"{store_id}.db").resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("store_id escapes the configured NanoJuris store root") from exc
    return candidate


def main() -> None:
    """Run the optional MCP server."""

    create_server().run()


if __name__ == "__main__":
    main()
