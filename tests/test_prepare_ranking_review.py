from __future__ import annotations

from tools.prepare_ranking_review import prepare


def test_prepare_ranking_review_creates_eighty_pending_rows_without_fabricating_grades() -> None:
    benchmark = {
        "ranking_version": "test-v1",
        "splits": {
            "development": [
                {"id": f"q{index:02d}", "query": f"query {index}"} for index in range(1, 6)
            ],
            "holdout": [
                {"id": f"q{index:02d}", "query": f"query {index}"} for index in range(6, 9)
            ],
        },
    }
    result = prepare(benchmark, {f"q{index:02d}": [] for index in range(1, 9)})
    assert result["query_count"] == 8
    assert result["row_count"] == 80
    assert result["human_validation_required"] is True
    assert all(row["human_grade"] is None for row in result["rows"])
    assert all(row["machine_prelabel"]["grade"] is None for row in result["rows"])


def test_prepare_ranking_review_preserves_machine_suggestion_separately() -> None:
    benchmark = {"splits": {"development": [{"id": "q01", "query": "tema"}]}}
    result = prepare(
        benchmark,
        {"q01": ["doc-1"]},
        top_k=1,
        suggestions={"q01:doc-1": {"grade": 2, "confidence": 0.5, "status": "machine"}},
    )
    row = result["rows"][0]
    assert row["machine_prelabel"]["grade"] == 2
    assert row["human_grade"] is None
