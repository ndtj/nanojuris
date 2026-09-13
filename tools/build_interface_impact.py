"""Build the provider interface-impact matrix used by release governance.

The matrix is intentionally descriptive: it derives surface declarations from
the canonical provider catalog and never changes rollout state.  A provider
can be present in the SDK while remaining blocked or opt-in for federation.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "docs" / "registry" / "provider-catalog.full.json"
DEFAULT_OUTPUT = ROOT / "docs" / "operations" / "interface-impact-matrix-20260902.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "docs" / "operations" / "interface-impact-matrix-20260902.md"
BLOCKED_STATUSES = {
    "blocked_access",
    "blocked_transport",
    "access_controlled",
    "source_unavailable",
}


def _runtime(entry: dict[str, Any]) -> bool:
    return entry.get("implementation_status") == "implemented" or entry.get("lifecycle") in {
        "implemented",
        "runtime",
    }


def _rollout_mode(entry: dict[str, Any]) -> str:
    if entry.get("lifecycle") == "candidate" or entry.get("category") == "research_candidate":
        return "opt_in"
    if entry.get("live_status") in BLOCKED_STATUSES or entry.get("maturity_tier") == "blocked":
        return "blocked"
    interfaces = entry.get("interfaces") or {}
    # Rollout mode must describe the same default-federation boundary as the
    # capability contract.  A runtime adapter that is deliberately withheld
    # (for example, because fixtures or a live check are still pending) is not
    # ``enabled`` merely because it can be imported by the SDK.
    if bool(interfaces.get("unified_search")):
        return "enabled"
    if bool(interfaces.get("opt_in_unified_search")):
        return "opt_in"
    return "not_exposed"


def build(catalog: Path = DEFAULT_CATALOG, *, generated_at: str | None = None) -> dict[str, Any]:
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    items: list[dict[str, Any]] = []
    for entry in sorted(payload.get("entries", []), key=lambda item: item.get("source_id", "")):
        interfaces = entry.get("interfaces") or {}
        output = entry.get("output_contract") or {}
        runtime = _runtime(entry)
        canonical = bool(output.get("canonical_records"))
        impact = {
            "sdk": runtime,
            "cli": bool(interfaces.get("cli")),
            "mcp": bool(interfaces.get("mcp")),
            "studio": bool(interfaces.get("studio")),
            "unified_search": bool(interfaces.get("unified_search")),
            "store": runtime and canonical,
            "exports": runtime and canonical,
        }
        missing = [surface for surface, declared in impact.items() if not declared]
        items.append(
            {
                "source_id": entry.get("source_id"),
                "display_name": entry.get("display_name"),
                "lifecycle": entry.get("lifecycle"),
                "category": entry.get("category"),
                "maturity_tier": entry.get("maturity_tier"),
                "rollout_mode": _rollout_mode(entry),
                "impact": impact,
                "missing_or_not_exposed": missing,
                "legacy_doc": (entry.get("documentation") or {}).get("legacy_doc"),
                "canonical_doc": (entry.get("documentation") or {}).get("human_doc"),
                "fixture_references": (entry.get("documentation") or {}).get(
                    "fixture_references", 0
                ),
                "safe_to_route": (entry.get("ai_usage") or {}).get("safe_to_route", False),
                "live_status": entry.get("live_status"),
            }
        )
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "schema_version": 1,
        "generated_at": timestamp,
        "source_catalog": str(catalog.as_posix()),
        "no_rollout_mutation": True,
        "items": items,
        "summary": {
            "providers": len(items),
            "runtime": sum(_runtime(entry) for entry in payload.get("entries", [])),
            "enabled": sum(item["rollout_mode"] == "enabled" for item in items),
            "opt_in": sum(item["rollout_mode"] == "opt_in" for item in items),
            "blocked": sum(item["rollout_mode"] == "blocked" for item in items),
            "unified_search": sum(item["impact"]["unified_search"] for item in items),
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Matriz de impacto de interfaces",
        "",
        "Artefato descritivo gerado do catálogo canônico; não altera rollout.",
        "",
        f"Providers: **{summary['providers']}**; runtime: **{summary['runtime']}**; "
        f"busca unificada: **{summary['unified_search']}**.",
        "",
        "| Provider | Modo | SDK | CLI | MCP | Studio | Federação | Store | Exports | Live |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in payload["items"]:
        impact = item["impact"]
        marks = ["sim" if impact[key] else "não" for key in ("sdk", "cli", "mcp", "studio")]
        marks += ["sim" if impact[key] else "não" for key in ("unified_search", "store", "exports")]
        lines.append(
            f"| `{item['source_id']}` | `{item['rollout_mode']}` | "
            f"{' | '.join(marks)} | `{item['live_status'] or 'not_observed'}` |"
        )
    lines += ["", "O modo `blocked`/`opt_in` nunca é convertido automaticamente em `enabled`.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    catalog = args.catalog if args.catalog.is_absolute() else ROOT / args.catalog
    output = args.output if args.output.is_absolute() else ROOT / args.output
    markdown_output = (
        args.markdown_output if args.markdown_output.is_absolute() else ROOT / args.markdown_output
    )
    payload = build(catalog, generated_at=args.generated_at)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {"output": str(output), **payload["summary"]}, ensure_ascii=False, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
