"""Build deterministic national coverage claims from the packaged topology."""

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

from nanojuris.topology import packaged_topology, project_coverage  # noqa: E402

DEFAULT_OUTPUT = ROOT / "docs" / "topology" / "national-coverage-claims-20260901.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "docs" / "topology" / "national-coverage-claims-20260901.md"


def build(
    *,
    topology_version: str = "2026-09-01",
    measured_at: str | None = None,
) -> dict[str, Any]:
    """Return generated claims, gap projections and finite epoch history."""

    projection = project_coverage(
        packaged_topology(topology_version=topology_version),
        measured_at=measured_at,
    )
    return projection.to_dict()


def write(output: Path, payload: dict[str, Any]) -> None:
    """Write a stable, human-readable JSON artifact."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def markdown(payload: dict[str, Any], *, source_name: str | None = None) -> str:
    """Render a concise human projection without replacing the JSON source."""

    lines = [
        "# Claims nacionais de cobertura de jurisprudência",
        "",
        f"Época: `{payload['epoch']['epoch_id']}` (corte `{payload['epoch']['cutoff_date']}`).",
        "",
        "Os percentuais medem bindings institucionais implementados na topologia; "
        "não significam acervo temporal integral nem disponibilidade live.",
        "",
        "## Claims gerados",
        "",
        "| Dimensão | Numerador | Denominador | Percentual | Medido em |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for claim in payload["claims"]:
        lines.append(
            f"| `{claim['dimension']}` | {claim['numerator']} | {claim['denominator']} | "
            f"{claim['ratio']:.2%} | {claim['measured_at']} |"
        )
    lines.extend(
        [
            "",
            "## Lacunas por ramo",
            "",
            "| Ramo | Collections sem provider implementado |",
            "| --- | ---: |",
        ]
    )
    for branch, count in payload["summary"]["gaps_by_branch"].items():
        lines.append(f"| `{branch}` | {count} |")
    lines.extend(
        [
            "",
            f"Total de lacunas emitidas: **{len(payload['gaps'])}**. "
            "A lista completa, com motivo e status, está no artefato JSON.",
            "",
            "## Histórico",
            "",
            "| Epoch | Versão da topologia | Data de corte |",
            "| --- | --- | --- |",
        ]
    )
    for epoch in payload["history"]:
        lines.append(
            f"| `{epoch['epoch_id']}` | `{epoch['topology_version']}` | {epoch['cutoff_date']} |"
        )
    source_name = source_name or DEFAULT_OUTPUT.name
    lines.extend(
        [
            "",
            f"Fonte machine-readable: `{source_name}`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--topology-version", default="2026-09-01")
    parser.add_argument(
        "--measured-at",
        help="ISO date of the measurement; defaults to the latest topology cutoff date",
    )
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    payload = build(topology_version=args.topology_version, measured_at=args.measured_at)
    write(output, payload)
    markdown_output = args.markdown_output
    if not markdown_output.is_absolute():
        markdown_output = ROOT / markdown_output
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(markdown(payload, source_name=output.name), encoding="utf-8")
    claims = {claim["dimension"]: claim["ratio"] for claim in payload["claims"]}
    print(
        json.dumps(
            {
                "output": str(output),
                "markdown_output": str(markdown_output),
                "epoch": payload["epoch"]["epoch_id"],
                "claims": claims,
                "gaps": len(payload["gaps"]),
                "history": len(payload["history"]),
                "network_access": payload["summary"]["network_access"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
