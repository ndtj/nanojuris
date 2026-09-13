"""Build the executable 27-court state appellate coverage program."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "docs/coverage/surface-state-registry-20260902.json"
DEFAULT_JSON = ROOT / "docs/coverage/state-appellate-program-20260905.json"
DEFAULT_MARKDOWN = ROOT / "docs/coverage/state-appellate-program-20260905.md"

GATES: tuple[tuple[str, str], ...] = (
    ("official_source", "Confirmar fonte oficial, rota publica e limites"),
    ("degree_contract", "Provar contrato especifico de segundo grau/CJSG"),
    ("adapter", "Implementar e registrar adapter com erros explicitos"),
    ("fixtures", "Cobrir sucesso, vazio, parametro invalido e schema drift"),
    ("pagination_filters", "Validar pagina 2, ordenacao e filtros"),
    ("live_validation", "Executar chamada live bounded com conteudo juridico"),
    ("quality", "Validar identidade, grau, trace e deduplicacao"),
    ("federation", "Habilitar federacao somente apos todos os gates"),
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _completed_gates(surface: dict[str, Any]) -> set[str]:
    provider = surface.get("provider")
    lifecycle = surface.get("lifecycle")
    contract = surface.get("contract_status")
    live = surface.get("live_status")
    federation = surface.get("federation_status")
    notes = str(surface.get("notes") or "")

    completed: set[str] = set()
    if provider:
        completed.add("official_source")
    if contract == "live_validated" or (lifecycle == "implemented" and "contrato proprio" in notes):
        completed.add("degree_contract")
    if lifecycle == "implemented":
        completed.add("adapter")
    if contract == "live_validated":
        completed.update({"fixtures", "pagination_filters", "quality"})
    if contract == "live_validated" and live == "valid":
        completed.add("live_validation")
    if federation == "enabled":
        completed.add("federation")
    return completed


def _action(surface: dict[str, Any], completed: set[str]) -> str:
    if len(completed) == len(GATES):
        return "maintenance"
    status_values = {
        str(surface.get("lifecycle") or ""),
        str(surface.get("live_status") or ""),
        str(surface.get("contract_status") or ""),
    }
    if status_values & {
        "blocked_access",
        "access_controlled",
        "blocked_transport",
        "transport_blocked",
        "source_unavailable",
    }:
        return "blocked_recheck"
    if not surface.get("provider") or surface.get("lifecycle") == "candidate":
        return "adapter_discovery"
    return "contract_hardening"


def build_program(registry: dict[str, Any], generated_at: str) -> dict[str, Any]:
    surfaces = [
        item
        for item in registry.get("surfaces", [])
        if item.get("branch") == "state"
        and item.get("degree") == "second"
        and item.get("collection") == "CJSG"
        and item.get("required") is True
    ]
    authorities = [str(item.get("authority")) for item in surfaces]
    duplicates = sorted(code for code, count in Counter(authorities).items() if count != 1)
    if len(surfaces) != 27 or len(set(authorities)) != 27 or duplicates:
        raise ValueError(
            "expected exactly 27 unique required state CJSG surfaces; "
            f"found rows={len(surfaces)}, unique={len(set(authorities))}, "
            f"duplicates={duplicates}"
        )

    workpacks: list[dict[str, Any]] = []
    for surface in sorted(surfaces, key=lambda item: str(item["authority"])):
        completed = _completed_gates(surface)
        tasks = [
            {
                "id": f"{surface['authority']}-CJSG-{index:02d}",
                "gate": gate,
                "title": title,
                "status": "completed" if gate in completed else "pending",
            }
            for index, (gate, title) in enumerate(GATES, start=1)
        ]
        workpacks.append(
            {
                "authority": surface["authority"],
                "surface_id": surface["surface_id"],
                "provider": surface.get("provider"),
                "lifecycle": surface.get("lifecycle"),
                "live_status": surface.get("live_status"),
                "contract_status": surface.get("contract_status"),
                "federation_status": surface.get("federation_status"),
                "action": _action(surface, completed),
                "completed_gates": len(completed),
                "total_gates": len(GATES),
                "evidence_ids": list(surface.get("evidence_ids") or []),
                "tasks": tasks,
            }
        )

    action_counts = Counter(item["action"] for item in workpacks)
    completed = sum(item["completed_gates"] == len(GATES) for item in workpacks)
    return {
        "schema_version": "state-appellate-program-v1",
        "generated_at": generated_at,
        "source_artifact": str(DEFAULT_REGISTRY.relative_to(ROOT)).replace("\\", "/"),
        "scope": {
            "branch": "state",
            "degree": "second",
            "collection": "CJSG",
            "expected_authorities": 27,
        },
        "summary": {
            "authorities": len(workpacks),
            "complete_8_of_8": completed,
            "incomplete": len(workpacks) - completed,
            "by_action": dict(sorted(action_counts.items())),
            "coverage_claim": f"{completed}/27",
        },
        "promotion_rule": (
            "8/8 gates: official source, degree contract, adapter, fixtures, "
            "pagination/filters, bounded live validation, quality and federation"
        ),
        "workpacks": workpacks,
    }


def render_markdown(program: dict[str, Any]) -> str:
    summary = program["summary"]
    lines = [
        "# Programa nacional de segundo grau dos TJs",
        "",
        f"Gerado em `{program['generated_at']}`. Nao editar a tabela manualmente.",
        "",
        "Cobertura significa oito gates comprovados por superficie; provider "
        "existente ou HTTP 200 isolado nao basta.",
        "",
        "## Resumo",
        "",
        f"- Tribunais: **{summary['authorities']}/27** mapeados.",
        f"- Workpacks completos: **{summary['complete_8_of_8']}/27**.",
        f"- Workpacks incompletos: **{summary['incomplete']}**.",
        "",
        "## Workpacks",
        "",
        "| TJ | Provider | Estado | Acao | Gates | Proxima tarefa |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for item in program["workpacks"]:
        next_task = next(
            (task["title"] for task in item["tasks"] if task["status"] == "pending"),
            "Revalidacao periodica",
        )
        lines.append(
            f"| `{item['authority']}` | `{item['provider'] or '-'}` | "
            f"`{item['contract_status'] or item['lifecycle']}` | `{item['action']}` | "
            f"{item['completed_gates']}/{item['total_gates']} | {next_task} |"
        )
    lines.extend(
        [
            "",
            "## Definicao dos gates",
            "",
        ]
    )
    for index, (gate, title) in enumerate(GATES, start=1):
        lines.append(f"{index}. `{gate}` - {title}.")
    lines.extend(
        [
            "",
            "Bloqueios de acesso/transporte permanecem explicitos e nunca sao "
            "convertidos em resultado vazio. Os detalhes executaveis de cada "
            "tribunal estao no array `workpacks` do JSON correspondente.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--generated-at", default=date.today().isoformat())
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    program = build_program(_load(args.registry), args.generated_at)
    if args.write:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(program, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        args.markdown_output.write_text(render_markdown(program), encoding="utf-8")
    else:
        print(json.dumps(program["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
