"""Build a deterministic readiness board for the next Juscraper adapter wave.

The board is an offline planning artifact.  It joins static semantic-diff
records with bounded live evidence, but it never calls a court, imports
Juscraper at runtime, creates fixtures, or promotes a provider.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SEMANTIC = ROOT / "docs" / "provider-discovery" / "juscraper-semantic-diff-20260901.json"
DEFAULT_SMOKE = ROOT / "docs" / "provider-discovery" / "juscraper-live-smoke-20260901.json"
DEFAULT_RECHECK = ROOT / "docs" / "provider-discovery" / "juscraper-live-recheck-20260901.json"
DEFAULT_CJPG_LIVE = ROOT / "docs" / "provider-discovery" / "tjes-cjpg-live-20260901.json"
DEFAULT_TJSP_CJPG_LIVE = ROOT / "docs" / "provider-discovery" / "tjsp-cjpg-live-20260901.json"
DEFAULT_TJTO_CJPG_LIVE = ROOT / "docs" / "provider-discovery" / "tjto-cjpg-live-20260901.json"
DEFAULT_TJRO_RECHECK = ROOT / "docs" / "provider-discovery" / "tjro-cjsg-live-recheck-20260901.json"
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "adapter-wave-board-20260901.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "provider-discovery" / "adapter-wave-board-20260901.md"

WAVE_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "work_item": "A1",
        "source_id": "tjes_jurisprudencia",
        "surface": "cjsg",
        "sdd": "0025",
        "priority": "P0",
        "collection": "second_degree",
        "resume_when": "reuso aprovado, fixtures proprias e contrato de paginacao fechado",
    },
    {
        "work_item": "A2",
        "source_id": "tjrn_jurisprudencia",
        "surface": "cjsg",
        "sdd": "0041",
        "priority": "P0",
        "collection": "second_degree",
        "resume_when": "rota publica voltar a responder sem bloqueio de acesso",
    },
    {
        "work_item": "A3",
        "source_id": "tjro_jurisprudencia",
        "surface": "cjsg",
        "sdd": "0042",
        "priority": "P1",
        "collection": "second_degree",
        "resume_when": "rota geral oficial, filtros e contrato forem reproduzidos",
    },
    {
        "work_item": "A4",
        "source_id": "tjto_ementa_detail",
        "surface": "detail",
        "sdd": "0043",
        "priority": "P1",
        "collection": "second_degree_detail",
        "resume_when": "rota de detalhe e pareamento com listagem forem comprovados",
    },
    {
        "work_item": "C1",
        "source_id": "tjes_cjpg",
        "surface": "cjpg",
        "sdd": "0044",
        "priority": "P2",
        "collection": "first_degree",
        "resume_when": "revisao de reuso aprovar a coleta e o contrato continuar estavel",
    },
    {
        "work_item": "C2",
        "source_id": "tjes_turma_recursal",
        "surface": "cjpg",
        "sdd": "0045",
        "priority": "P2",
        "collection": "review_panel",
        "resume_when": "binding de turma recursal e semantica propria forem confirmados",
    },
    {
        "work_item": "C3",
        "source_id": "tjsp_cjpg",
        "surface": "cjpg",
        "sdd": "0046",
        "priority": "P2",
        "collection": "first_degree",
        "resume_when": "rota CJPG oficial e contrato independente forem confirmados",
    },
    {
        "work_item": "C4",
        "source_id": "tjto_cjpg",
        "surface": "cjpg",
        "sdd": "0047",
        "priority": "P2",
        "collection": "first_degree",
        "resume_when": "rota CJPG oficial e separacao de grau forem confirmadas",
    },
)


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"artifact invalido: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"artifact deve ser objeto JSON: {path}")
    return value


def _records(
    payload: dict[str, Any], key: str = "records"
) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in payload.get(key, []):
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id", row.get("provider", "")))
        surface = str(row.get("surface", "cjsg"))
        if source_id:
            result[(source_id, surface)] = row
    return result


def _live_state(
    source_id: str,
    smoke: dict[tuple[str, str], dict[str, Any]],
    recheck: dict[tuple[str, str], dict[str, Any]],
    dedicated: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> tuple[str, str]:
    # A recheck is newer evidence and intentionally overrides the historical
    # smoke result for readiness, while both references remain in the board.
    for key, rows in (("dedicated", dedicated or {}), ("recheck", recheck), ("smoke", smoke)):
        for (candidate, _surface), row in rows.items():
            if candidate != source_id:
                continue
            classification = str(
                row.get("classification", row.get("retrieval_status", "not_recorded"))
            )
            status = row.get("http_status", row.get("status"))
            return classification, f"{key}:http_{status}"
    return "not_recorded", "none"


def _readiness(item: dict[str, Any], semantic: dict[str, Any], live: str) -> tuple[str, str]:
    status = str(semantic.get("status", "surface_not_declared"))
    source_id = str(item["source_id"])
    surface = str(item["surface"])
    if live == "blocked_access":
        return (
            "blocked_access",
            "replay publico sem bloqueio e evidencias negativas antes de parser",
        )
    if source_id == "tjes_jurisprudencia" and live == "reachable_valid_data":
        return (
            "candidate_ready_for_contract_closure",
            "fechar reuso, fixtures e limites; nao promover ainda",
        )
    if source_id == "tjes_cjpg" and live == "reachable_valid_data":
        return (
            "separate_collection_contract",
            "revisar reuso e manter opt-in; nao misturar com CJSG ou processo",
        )
    if source_id == "tjto_ementa_detail" or status == "detail_contract_unverified":
        return "detail_contract_unverified", "reproduzir detalhe lazy, pareamento e falhas parciais"
    if surface == "cjpg" or status == "out_of_scope":
        return (
            "separate_collection_contract",
            "abrir contrato da collection sem misturar CJSG/processo",
        )
    if status == "no_runtime_equivalent":
        return (
            "candidate_needs_independent_contract",
            "provar rota, payload, identidade e semantica",
        )
    return (
        "covered_requires_differential_fixture",
        "capturar fixture propria e executar comparacao diferencial",
    )


def build(
    *,
    semantic_path: Path = DEFAULT_SEMANTIC,
    smoke_path: Path = DEFAULT_SMOKE,
    recheck_path: Path = DEFAULT_RECHECK,
    cjpg_live_path: Path = DEFAULT_CJPG_LIVE,
    tjro_recheck_path: Path = DEFAULT_TJRO_RECHECK,
    generated_at: str | None = None,
) -> dict[str, Any]:
    semantic_payload = _read(semantic_path)
    smoke_payload = _read(smoke_path)
    recheck_payload = _read(recheck_path)
    cjpg_live_payload = _read(cjpg_live_path)
    tjsp_cjpg_live_payload = _read(DEFAULT_TJSP_CJPG_LIVE)
    tjto_cjpg_live_payload = _read(DEFAULT_TJTO_CJPG_LIVE)
    tjro_recheck_payload = _read(tjro_recheck_path)
    semantic_records = _records(semantic_payload)
    smoke_records = _records(smoke_payload, "results")
    recheck_records = _records(recheck_payload, "results")
    cjpg_live_records = _records(cjpg_live_payload, "results")
    cjpg_live_records.update(_records(tjsp_cjpg_live_payload, "results"))
    cjpg_live_records.update(_records(tjto_cjpg_live_payload, "results"))
    cjpg_live_records.update(_records(tjro_recheck_payload, "results"))
    # The CJPG check is kept in its own artifact so that a first-degree
    # contract can be evidenced without changing historical Juscraper smoke
    # results for the unrelated CJSG surface.
    rows: list[dict[str, Any]] = []
    for item in WAVE_ITEMS:
        source_id = str(item["source_id"])
        surface = str(item["surface"])
        semantic = semantic_records.get((source_id, surface), {})
        live, live_evidence = _live_state(
            source_id, smoke_records, recheck_records, cjpg_live_records
        )
        readiness, next_gate = _readiness(item, semantic, live)
        rows.append(
            {
                **item,
                "semantic_status": str(semantic.get("status", "surface_not_declared")),
                "semantic_equivalent": semantic.get("nanojuris_equivalent"),
                "live_classification": live,
                "live_evidence": live_evidence,
                "readiness": readiness,
                "next_gate": next_gate,
                "runtime_promotion": "forbidden_until_0031_0034_and_human_review",
                "evidence": {
                    "semantic_diff": semantic_path.name,
                    "historical_smoke": smoke_path.name,
                    "recheck": recheck_path.name,
                    "dedicated_cjpg": cjpg_live_path.name,
                    "dedicated_tjsp_cjpg": DEFAULT_TJSP_CJPG_LIVE.name,
                    "dedicated_tjto_cjpg": DEFAULT_TJTO_CJPG_LIVE.name,
                    "dedicated_tjro_recheck": tjro_recheck_path.name,
                },
            }
        )
    generated = generated_at or datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 1,
        "generated_at": generated,
        "audit_mode": "offline_readiness_join_no_network",
        "upstream_commit": semantic_payload.get("upstream", {}).get("commit"),
        "no_runtime_promotion": True,
        "wave": "juscraper-adapter-waves",
        "items": rows,
        "summary": {
            "items": len(rows),
            "by_readiness": dict(Counter(row["readiness"] for row in rows)),
            "by_priority": dict(Counter(row["priority"] for row in rows)),
        },
        "limitations": [
            "A classificacao combina evidencia estatica e fotografias live bounded; "
            "nao fecha contrato.",
            "Nenhum corpo de resposta foi promovido a fixture ou federacao padrao.",
            "Reuso, equivalencia, identidade e seguranca continuam gates por pacote.",
        ],
    }


def to_markdown(board: dict[str, Any]) -> str:
    state_text = json.dumps(board["summary"]["by_readiness"], ensure_ascii=False, sort_keys=True)
    lines = [
        "# Fila da proxima onda de adapters (2026-09-01)",
        "",
        "Quadro offline de prontidao. Ele nao chama fontes, nao copia Juscraper "
        "e nao promove providers.",
        "",
        f"- Commit upstream: `{board.get('upstream_commit')}`",
        f"- Itens: **{board['summary']['items']}**",
        f"- Estados: `{state_text}`",
        "",
        "| Onda | Source ID | Superficie | Prioridade | Evidencia live mais "
        "recente | Estado | Proxima trava |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in board["items"]:
        row_text = (
            "| {work_item} | `{source_id}` | `{surface}` | {priority} | "
            "`{live_classification}` ({live_evidence}) | `{readiness}` | "
            "{next_gate} |"
        ).format(**row)
        lines.append(row_text)
    lines.extend(["", "## Regras de retomada", ""])
    for row in board["items"]:
        lines.append(f"- **{row['work_item']} / {row['source_id']}**: {row['resume_when']}.")
    lines.extend(["", "## Limites", ""])
    lines.extend(f"- {value}" for value in board["limitations"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semantic", type=Path, default=DEFAULT_SEMANTIC)
    parser.add_argument("--smoke", type=Path, default=DEFAULT_SMOKE)
    parser.add_argument("--recheck", type=Path, default=DEFAULT_RECHECK)
    parser.add_argument("--cjpg-live", type=Path, default=DEFAULT_CJPG_LIVE)
    parser.add_argument("--tjro-recheck", type=Path, default=DEFAULT_TJRO_RECHECK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    board = build(
        semantic_path=args.semantic,
        smoke_path=args.smoke,
        recheck_path=args.recheck,
        cjpg_live_path=args.cjpg_live,
        tjro_recheck_path=args.tjro_recheck,
        generated_at=args.generated_at,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(board, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(to_markdown(board), encoding="utf-8")
    print(json.dumps(board["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
