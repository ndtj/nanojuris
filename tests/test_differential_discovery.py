from __future__ import annotations

from nanojuris.discovery.differential import compare_filter_runs, compare_pages


def test_compare_pages_detects_overlap_without_using_total_zero_as_truth() -> None:
    result = compare_pages(
        {"source": "tj", "results": [{"id": "1"}], "total": 0, "total_known": False},
        {"source": "tj", "results": [{"id": "1"}], "total": 0, "total_known": False},
    )
    assert result["duplicate_page"] is True
    assert result["total_known"] is False
    assert result["total_match"] is None


def test_filter_comparison_does_not_call_a_blocked_response_empty() -> None:
    result = compare_filter_runs(
        {"status": "valid", "results": [{"id": "1"}, {"id": "2"}]},
        {"status": "blocked", "results": []},
    )
    assert result["status"] == "blocked"
    assert result["effect_observed"] is False
    assert result["removed_count"] == 2
