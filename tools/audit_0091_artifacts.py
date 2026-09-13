"""Audit generated artifacts and TODO markers for the 0091 handoff."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

OUTPUT = ROOT / "docs" / "coverage" / "0091-artifact-audit-20260908.json"
MARKDOWN_OUTPUT = ROOT / "docs" / "coverage" / "0091-artifact-audit-20260908.md"
SCAN_ROOTS = (
    "src/nanojuris",
    "tools",
    "tests",
    "specs/changes/0091-national-coverage-gold-handoff",
)
IGNORED_PARTS = {"fixtures", "__pycache__", ".git"}


def build(root: Path = ROOT) -> dict[str, Any]:
    todo_hits: list[dict[str, Any]] = []
    files_scanned = 0
    for relative_root in SCAN_ROOTS:
        base = root / relative_root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
                continue
            if path.suffix.lower() not in {".py", ".md", ".json", ".ts", ".tsx"}:
                continue
            files_scanned += 1
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                if any(token in line.upper() for token in ("TODO", "FIXME", "XXX")):
                    todo_hits.append(
                        {
                            "path": str(path.relative_to(root)).replace("\\", "/"),
                            "line": line_number,
                            "text": line.strip()[:240],
                        }
                    )
    catalog = _json(root / "docs/registry/provider-catalog.full.json")
    runtime = _json(root / "docs/registry/providers.json")
    workpacks = _json(
        root / "specs/changes/0091-national-coverage-gold-handoff/surface-workpacks/manifest.json"
    )
    return {
        "schema_version": "0091-artifact-audit-v1",
        "network_access": "not_used",
        "files_scanned": files_scanned,
        "todo_hits": todo_hits,
        "todo_policy": "reported_not_silently_deleted",
        "catalog_runtime": {
            "catalog_entries": len(catalog.get("entries", [])),
            "runtime_entries": len(runtime.get("implemented", [])),
            "divergence": sorted(
                set(runtime.get("implemented", []))
                - {row.get("source_id") for row in catalog.get("entries", [])}
            ),
        },
        "surface_workpacks": {
            "surface_count": workpacks.get("surface_count", 0),
            "required_surface_count": workpacks.get("required_surface_count", 0),
            "complete_gate_count": workpacks.get("complete_gate_count", 0),
        },
        "open_tasks_are_explicit": True,
        "status": "audit_complete_with_reported_todos",
    }


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# 0091 artifact audit",
        "",
        "Offline audit; TODO/FIXME markers are reported, not deleted automatically.",
        "",
        f"- Files scanned: **{payload['files_scanned']}**",
        f"- TODO-like markers: **{len(payload['todo_hits'])}**",
        f"- Catalog/runtime divergence: **{len(payload['catalog_runtime']['divergence'])}**",
        f"- Surface workpacks: **{payload['surface_workpacks']['surface_count']}**",
        "",
        "## Markers",
        "",
    ]
    if payload["todo_hits"]:
        lines.extend(
            f"- `{item['path']}:{item['line']}` — {item['text']}" for item in payload["todo_hits"]
        )
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    payload = build(root)
    if args.write:
        output = root / OUTPUT.relative_to(ROOT)
        markdown = root / MARKDOWN_OUTPUT.relative_to(ROOT)
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        markdown.write_text(render(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
