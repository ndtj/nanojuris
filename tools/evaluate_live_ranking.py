"""Evaluate deterministic ranking outputs against human judgment labels."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _dcg(values: list[int], cutoff: int) -> float:
    return sum((2**grade - 1) / math.log2(index + 2) for index, grade in enumerate(values[:cutoff]))


def _metrics(ranked: list[str], labels: dict[str, int]) -> dict[str, float | None]:
    if not labels:
        return {
            "ndcg_at_10": None,
            "precision_at_5": None,
            "mrr_at_10": None,
            "irrelevant_at_5": None,
        }
    grades = [int(labels.get(document_id, 0)) for document_id in ranked]
    ideal = sorted(labels.values(), reverse=True)
    ideal_dcg = _dcg(ideal, 10)
    relevant_top5 = sum(grade >= 2 for grade in grades[:5])
    first_relevant = next(
        (index + 1 for index, grade in enumerate(grades[:10]) if grade >= 2), None
    )
    return {
        "ndcg_at_10": round(_dcg(grades, 10) / ideal_dcg, 6) if ideal_dcg else 0.0,
        "precision_at_5": round(relevant_top5 / min(5, len(ranked)), 6) if ranked else 0.0,
        "mrr_at_10": round(1 / first_relevant, 6) if first_relevant else 0.0,
        "irrelevant_at_5": round(1 - (relevant_top5 / min(5, len(ranked))), 6) if ranked else 0.0,
    }


def evaluate(payload: dict[str, Any], rankings: dict[str, list[str]]) -> dict[str, Any]:
    labels: dict[str, dict[str, int]] = {}
    for judgment in payload.get("judgments", []):
        if not isinstance(judgment, dict):
            continue
        labels.setdefault(str(judgment.get("query_id", "")), {})[
            str(judgment.get("document_id", ""))
        ] = int(judgment.get("grade", 0))
    if not labels:
        return {"status": "pending_labels", "query_count": len(rankings), "metrics": {}}
    per_query = {
        query_id: _metrics(ranked, labels.get(query_id, {}))
        for query_id, ranked in rankings.items()
    }
    numeric = [value for value in per_query.values() if value["ndcg_at_10"] is not None]
    return {
        "status": "evaluated",
        "query_count": len(per_query),
        "metrics": {
            key: round(sum(float(item[key]) for item in numeric) / len(numeric), 6)
            for key in ("ndcg_at_10", "precision_at_5", "mrr_at_10", "irrelevant_at_5")
        }
        if numeric
        else {},
        "per_query": per_query,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", type=Path)
    parser.add_argument(
        "--rankings", type=Path, help="JSON object mapping query_id to ordered document IDs"
    )
    args = parser.parse_args()
    payload = json.loads(args.benchmark.read_text(encoding="utf-8"))
    rankings = json.loads(args.rankings.read_text(encoding="utf-8")) if args.rankings else {}
    print(json.dumps(evaluate(payload, rankings), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
