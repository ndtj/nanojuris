"""Audit provider interface declarations before a release rehearsal.

The audit is offline and read-only.  It checks that catalog entries expose a
complete interface declaration, that documentation links exist, and that
candidates/blocked sources cannot be advertised as enabled.  It is a guard,
not a promotion mechanism.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "docs" / "registry" / "provider-catalog.full.json"
DEFAULT_OUTPUT = ROOT / "docs" / "operations" / "release-compatibility-20260902.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "docs" / "operations" / "release-compatibility-20260902.md"
SURFACES = ("cli", "mcp", "studio", "unified_search")
BLOCKED = {"blocked_access", "blocked_transport", "access_controlled", "source_unavailable"}


def _resolve_doc(path_value: Any) -> bool:
    if not isinstance(path_value, str) or not path_value:
        return False
    return (
        (ROOT / path_value).is_file()
        if not Path(path_value).is_absolute()
        else Path(path_value).is_file()
    )


def build(catalog: Path = DEFAULT_CATALOG, *, generated_at: str | None = None) -> dict[str, Any]:
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    for entry in sorted(payload.get("entries", []), key=lambda item: item.get("source_id", "")):
        source = str(entry.get("source_id") or "")
        interfaces = entry.get("interfaces") or {}
        documentation = entry.get("documentation") or {}
        runtime = entry.get("implementation_status") in {"implemented", "runtime"} or entry.get(
            "lifecycle"
        ) in {"implemented", "runtime"}
        candidate = (
            entry.get("lifecycle") == "candidate" or entry.get("category") == "research_candidate"
        )
        blocked = entry.get("live_status") in BLOCKED or entry.get("maturity_tier") == "blocked"
        checks = {
            "source_id": bool(source),
            "interfaces_object": isinstance(interfaces, dict),
            "legacy_doc_exists": _resolve_doc(documentation.get("legacy_doc")),
            "canonical_doc_exists": _resolve_doc(documentation.get("human_doc")),
            "candidate_not_enabled": not candidate or not bool(interfaces.get("unified_search")),
            # A blocked source may remain declared in federation so the caller
            # receives an explicit access outcome; it must never be silent.
            "blocked_status_explicit": not blocked or bool(entry.get("live_status")),
        }
        missing_surfaces = [surface for surface in SURFACES if surface not in interfaces]
        checks["surface_keys_complete"] = not missing_surfaces
        results.append(
            {
                "source_id": source,
                "runtime": runtime,
                "candidate": candidate,
                "blocked": blocked,
                "checks": checks,
                "missing_surface_keys": missing_surfaces,
                "status": "pass" if all(checks.values()) else "fail",
            }
        )
    failures = [item for item in results if item["status"] != "pass"]
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "schema_version": 1,
        "generated_at": timestamp,
        "source_catalog": catalog.as_posix(),
        "audit_mode": "offline_read_only",
        "promotion_performed": False,
        "checks": results,
        "summary": {
            "providers": len(results),
            "passed": len(results) - len(failures),
            "failed": len(failures),
            "runtime": sum(item["runtime"] for item in results),
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Auditoria de compatibilidade de release",
        "",
        "Auditoria offline e somente leitura; não promove providers.",
        "",
        f"**{summary['passed']}/{summary['providers']}** entradas passaram; "
        f"falhas: **{summary['failed']}**.",
        "",
        "| Provider | Runtime | Candidato | Bloqueado | Resultado | Falhas |",
        "|---|---:|---:|---:|---|---|",
    ]
    for item in payload["checks"]:
        failed = [name for name, passed in item["checks"].items() if not passed]
        lines.append(
            f"| `{item['source_id']}` | {'sim' if item['runtime'] else 'não'} | "
            f"{'sim' if item['candidate'] else 'não'} | {'sim' if item['blocked'] else 'não'} | "
            f"`{item['status']}` | {', '.join(failed) or '—'} |"
        )
    lines += ["", "Aprovação jurídica, publicação e deploy permanecem gates externos.", ""]
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
    return 0 if payload["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
