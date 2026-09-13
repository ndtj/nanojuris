from __future__ import annotations

from tools.benchmark_live_ranking import benchmark


def test_live_ranker_240_candidate_budget_is_cpu_bounded() -> None:
    result = benchmark(rounds=5, candidates=240)
    assert result["network_calls"] == 0
    assert result["status"] == "passed"
    assert result["latency_ms"]["p95"] < 150
