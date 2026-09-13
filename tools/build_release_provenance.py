"""Build a local SBOM and provenance manifest without publishing anything.

The manifest contains direct dependency specifiers, project/file hashes and
the operator's local-operation decision.  Local/federated technical use does
not require an additional internal license or judicial-authorization gate;
redistribution remains a separate, explicitly false release property.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import tomllib

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "operations" / "release-provenance-20260902.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "docs" / "operations" / "release-provenance-20260902.md"
HASH_FILES = (
    Path("pyproject.toml"),
    Path("LICENSE"),
    Path("src/nanojuris/__init__.py"),
    Path("docs/registry/provider-catalog.full.json"),
)
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+")


def _git(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dependency(specifier: str) -> dict[str, Any]:
    match = NAME_RE.match(specifier)
    name = match.group(0) if match else specifier
    return {
        "type": "library",
        "name": name,
        "bom-ref": f"pkg:pypi/{name.lower()}",
        "properties": [{"name": "dependency_specifier", "value": specifier}],
        "licenses": [],
    }


def build(*, generated_at: str | None = None) -> dict[str, Any]:
    project_data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = project_data.get("project", {})
    dependencies = [str(item) for item in project.get("dependencies", [])]
    optional = project.get("optional-dependencies", {})
    for _group, values in sorted(optional.items()):
        dependencies.extend(str(item) for item in values)
    catalog = json.loads(
        (ROOT / "docs/registry/provider-catalog.full.json").read_text(encoding="utf-8")
    )
    entries = catalog.get("entries", [])
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    files = [
        {
            "path": path.as_posix(),
            "sha256": _sha256(ROOT / path),
        }
        for path in HASH_FILES
    ]
    return {
        "schema_version": 1,
        "generated_at": timestamp,
        "audit_mode": "local_release_rehearsal_read_only",
        "production_action_performed": False,
        "bom": {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "metadata": {
                "timestamp": timestamp,
                "component": {
                    "type": "library",
                    "name": project.get("name", "nanojuris"),
                    "version": project.get("version"),
                    "licenses": [{"license": {"id": "MIT"}}],
                },
            },
            "components": [_dependency(item) for item in sorted(dependencies)],
        },
        "provenance": {
            "git_commit": _git("rev-parse", "HEAD"),
            "git_tree_state": "dirty" if _git("status", "--porcelain") else "clean",
            "hashed_files": files,
            "source_catalog_entries": len(entries),
            "runtime_providers": sum(
                item.get("implementation_status") in {"runtime", "implemented"} for item in entries
            ),
            "technical_operation_authorized": True,
            "license_review": "not_required_for_local_federation",
            "redistribution_authorized": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    bom = payload["bom"]
    provenance = payload["provenance"]
    lines = [
        "# Provenance e SBOM local",
        "",
        "Artefato de release rehearsal somente leitura; não publica nem altera produção.",
        "",
        f"Projeto: **{bom['metadata']['component']['name']} "
        f"{bom['metadata']['component']['version']}**.",
        f"Componentes diretos (incluindo extras): **{len(bom['components'])}**.",
        f"Providers catalogados/runtime: **{provenance['source_catalog_entries']}/"
        f"{provenance['runtime_providers']}**.",
        "",
        "## Arquivos com hash",
        "",
        "| Arquivo | SHA-256 |",
        "|---|---|",
    ]
    for item in provenance["hashed_files"]:
        lines.append(f"| `{item['path']}` | `{item['sha256'] or 'missing'}` |")
    lines += [
        "",
        f"Operação técnica local: **{provenance['license_review']}**; "
        "redistribuição autorizada: **não**.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    markdown_output = (
        args.markdown_output if args.markdown_output.is_absolute() else ROOT / args.markdown_output
    )
    payload = build(generated_at=args.generated_at)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "components": len(payload["bom"]["components"]),
                **payload["provenance"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
