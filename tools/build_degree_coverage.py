"""Build the national CJPG/CJSG and branch-specific coverage matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = str(ROOT / "src")
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)

from nanojuris.coverage_matrix import build_degree_matrix  # noqa: E402

DEFAULT_OUTPUT = ROOT / "docs" / "topology" / "degree-coverage-matrix-20260901.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "docs" / "topology" / "degree-coverage-matrix-20260901.md"


def build(*, version: str = "2026-09-01", generated_at: str = "2026-09-01") -> dict[str, Any]:
    """Return a deterministic, offline matrix payload."""

    return build_degree_matrix(version=version, generated_at=generated_at).to_dict()


def write(output: Path, payload: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Matriz nacional por coleção e grau",
        "",
        f"Versão: `{payload['version']}` — geração `{payload['generated_at']}`.",
        "",
        "`CJPG` representa primeiro grau e `CJSG` segundo grau somente quando a "
        "coleção é comprovada pela fonte. As demais superfícies mantêm sua "
        "nomenclatura nativa.",
        "",
        "## Resumo",
        "",
        f"- Superfícies totais: **{summary['surface_count']}**",
        f"- Superfícies obrigatórias: **{summary['required_surface_count']}**",
        f"- Lacunas obrigatórias: **{summary['gap_count']}**",
        f"- Superfícies consultáveis: **{summary['queryable_count']}**",
        "",
        "### CJPG/CJSG",
        "",
        "| Coleção | Implementadas | Esperadas | Cobertura |",
        "| --- | ---: | ---: | ---: |",
    ]
    for collection in ("CJPG", "CJSG"):
        row = summary["by_collection"].get(
            collection, {"implemented": 0, "expected": 0, "ratio": 0.0}
        )
        lines.append(
            f"| `{collection}` | {row['implemented']} | {row['expected']} | {row['ratio']:.2%} |"
        )
    lines.extend(
        [
            "",
            "### Por ramo",
            "",
            "| Ramo | Linhas obrigatórias |",
            "| --- | ---: |",
        ]
    )
    for branch, count in summary["by_branch"].items():
        lines.append(f"| `{branch}` | {count} |")
    lines.extend(
        [
            "",
            "### Lacunas e contratos pendentes",
            "",
            "| Autoridade | Ramo | Grau | Coleção | Status | Provider | Observação |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload["gaps"]:
        lines.append(
            f"| `{item['authority']}` | `{item['branch']}` | `{item['degree']}` | "
            f"`{item['collection']}` | `{item['status']}` | "
            f"{('`' + item['provider'] + '`') if item['provider'] else '—'} | "
            f"{item['notes'] or '—'} |"
        )
    lines.extend(
        [
            "",
            "## Matriz completa",
            "",
            "| Autoridade | Ramo | Grau | Coleção | Status | Provider | "
            "Obrigatória | Consultável |",
            "| --- | --- | --- | --- | --- | --- | ---: | ---: |",
        ]
    )
    for item in payload["surfaces"]:
        lines.append(
            f"| `{item['authority']}` | `{item['branch']}` | `{item['degree']}` | "
            f"`{item['collection']}` | `{item['status']}` | "
            f"{('`' + item['provider'] + '`') if item['provider'] else '—'} | "
            f"{'sim' if item['required'] else 'não'} | {'sim' if item['queryable'] else 'não'} |"
        )
    lines.extend(
        [
            "",
            "A matriz mede linhas esperadas mapeadas. Não afirma que todos os "
            "documentos históricos estejam disponíveis nem que uma fonte live "
            "permaneça sempre acessível.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--version", default="2026-09-01")
    parser.add_argument("--generated-at", default="2026-09-01")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    markdown_output = (
        args.markdown_output if args.markdown_output.is_absolute() else ROOT / args.markdown_output
    )
    payload = build(version=args.version, generated_at=args.generated_at)
    write(output, payload)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "markdown_output": str(markdown_output),
                "surface_count": payload["summary"]["surface_count"],
                "gap_count": payload["summary"]["gap_count"],
                "cjpg": payload["summary"]["by_collection"]["CJPG"],
                "cjsg": payload["summary"]["by_collection"]["CJSG"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
