"""Prepare the bounded human-review matrix for the live-ranking benchmark.

The tool creates exactly ``query_count * top_k`` review rows.  It may attach a
machine suggestion when a caller supplies a pre-scored candidate map, but it
never writes a human grade and never treats a missing candidate as an
irrelevant legal decision.  This keeps the benchmark honest when a live smoke
has no persisted result bodies or only redacted metadata.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _queries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for split in payload.get("splits", {}).values()
        for item in split
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    ]


def prepare(
    benchmark: dict[str, Any],
    rankings: dict[str, list[str]],
    *,
    top_k: int = 10,
    suggestions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    suggestions = suggestions or {}
    rows: list[dict[str, Any]] = []
    for query in _queries(benchmark):
        query_id = str(query["id"])
        ranked = [str(value) for value in rankings.get(query_id, [])[:top_k]]
        for rank in range(1, top_k + 1):
            document_id = ranked[rank - 1] if rank <= len(ranked) else None
            suggestion = suggestions.get(f"{query_id}:{document_id}") if document_id else None
            if suggestion is None:
                suggestion = {
                    "grade": None,
                    "confidence": 0.0,
                    "status": "not_scored_without_candidate_evidence",
                    "reason": (
                        "No persisted canonical result body or machine feature set is available."
                    ),
                }
            rows.append(
                {
                    "review_id": f"{query_id}:rank-{rank:02d}",
                    "query_id": query_id,
                    "query": str(query.get("query", "")),
                    "split": next(
                        (
                            split
                            for split, items in benchmark.get("splits", {}).items()
                            if any(item is query for item in items)
                        ),
                        "unknown",
                    ),
                    "rank": rank,
                    "document_id": document_id,
                    "machine_prelabel": suggestion,
                    "human_grade": None,
                    "human_reviewer": None,
                    "status": "pending_human_validation",
                }
            )
    return {
        "schema_version": "legal-live-ranking-review-v1",
        "generated_from": "docs/benchmarks/live-ranking-v1.json",
        "ranking_version": benchmark.get("ranking_version", "unknown"),
        "top_k": top_k,
        "query_count": len(_queries(benchmark)),
        "row_count": len(rows),
        "prelabel_status": "machine_prelabels_only",
        "human_validation_required": True,
        "rows": rows,
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Matriz de revisão do ranking live — 2026-09-09",
        "",
        "São 80 linhas (8 consultas × top 10). `machine_prelabel` é apenas uma",
        "sugestão técnica; `human_grade` permanece vazio até a validação do",
        "mantenedor. Não avaliar ausência de candidato como irrelevância.",
        "",
        "Escala humana: `0` irrelevante · `1` relacionado, mas não responde ·",
        "`2` relevante · `3` altamente relevante.",
        "",
        "| ID | Split | Consulta | Rank | Documento | Pré-rótulo | Grau humano | Status |",
        "|---|---|---|---:|---|---|---:|---|",
    ]
    for row in payload["rows"]:
        suggestion = row["machine_prelabel"]
        grade = suggestion.get("grade")
        suggestion_text = "—" if grade is None else str(grade)
        document = row["document_id"] or "(não persistido)"
        query = row["query"].replace("|", "\\|")
        lines.append(
            f"| `{row['review_id']}` | {row['split']} | {query} | {row['rank']} | "
            f"`{document}` | {suggestion_text} |  | {row['status']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--suggestions", type=Path)
    args = parser.parse_args()
    benchmark = json.loads(args.benchmark.read_text(encoding="utf-8"))
    rankings = json.loads(args.rankings.read_text(encoding="utf-8"))
    suggestions = (
        json.loads(args.suggestions.read_text(encoding="utf-8")) if args.suggestions else None
    )
    result = prepare(benchmark, rankings, suggestions=suggestions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(_markdown(result), encoding="utf-8")
    print(
        json.dumps(
            {key: result[key] for key in ("query_count", "row_count", "prelabel_status")},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
