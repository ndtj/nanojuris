from __future__ import annotations

import json
from pathlib import Path

from tools.evaluate_live_ranking import evaluate

ROOT = Path(__file__).parents[1]


def test_benchmark_contains_required_queries_and_explicit_pending_state() -> None:
    payload = json.loads(
        (ROOT / "docs" / "benchmarks" / "live-ranking-v1.json").read_text(encoding="utf-8")
    )
    queries = [item["query"] for split in payload["splits"].values() for item in split]
    assert "responsabilidade civil administrativa" in queries
    assert "acórdãos sobre divórcio" in queries
    assert any(item["intent"] == ["exact_identifier"] for item in payload["splits"]["holdout"])
    assert payload["judgment_status"] == "pending_human_labels"


def test_metric_tool_does_not_invent_scores_without_labels() -> None:
    payload = {"judgments": []}
    result = evaluate(payload, {"q01": ["doc-1"]})
    assert result == {"status": "pending_labels", "query_count": 1, "metrics": {}}


def test_metric_tool_calculates_ndcg_and_precision() -> None:
    payload = {
        "judgments": [
            {"query_id": "q", "document_id": "a", "grade": 3},
            {"query_id": "q", "document_id": "b", "grade": 0},
        ]
    }
    result = evaluate(payload, {"q": ["a", "b"]})
    assert result["status"] == "evaluated"
    assert result["metrics"]["precision_at_5"] == 0.5
    assert result["metrics"]["mrr_at_10"] == 1.0
