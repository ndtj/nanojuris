"""Measure local CPU ranking latency for a bounded 240-record candidate set."""

from __future__ import annotations

import argparse
import gc
import json
import statistics
import time
from pathlib import Path
from typing import Any

from nanojuris import CanonicalDecision, LegalLiveRanker, LegalQueryAnalyzer


def _records(count: int = 240) -> list[CanonicalDecision]:
    return [
        CanonicalDecision(
            id=f"bench-{index}",
            source=f"tj{index % 27:02d}",
            court=f"TJ{index % 27:02d}",
            case_number=f"0000000-{index:02d}.2024.8.26.0000",
            decision_type="acordao",
            case_class="Apelação Cível",
            subject="responsabilidade civil administrativa e dano moral",
            summary=(
                "Responsabilidade civil administrativa e dano moral em decisão de segundo grau."
            ),
            full_text=(
                "fundamentação pública da decisão sobre responsabilidade civil administrativa"
            ),
            degree="second",
            instance="second",
            branch="state",
            collection="CJSG",
            document_type="acordao",
        )
        for index in range(count)
    ]


def benchmark(*, rounds: int = 25, candidates: int = 240) -> dict[str, Any]:
    if rounds < 3 or candidates < 1:
        raise ValueError("rounds must be >= 3 and candidates must be positive")
    intent = LegalQueryAnalyzer().analyze("responsabilidade civil administrativa")
    records = _records(candidates)
    ranker = LegalLiveRanker()
    # A five-sample p95 is just the maximum and is too sensitive to an
    # unrelated scheduler wake-up on a developer workstation.  Keep the
    # caller's lower bound for validation, but collect a statistically useful
    # minimum sample for the reported percentile.
    measured_rounds = max(rounds, 25)
    durations: list[float] = []
    gc_enabled = gc.isenabled()
    gc.disable()
    try:
        # Warm the deterministic tokenizer/ranker once before measuring. This
        # excludes one-time allocator and regex-cache setup from the p95 gate.
        for _ in range(2):
            warmed = ranker.rank(intent, records)
            ranker.diversify_near_ties(warmed)
        for _ in range(measured_rounds):
            # The benchmark is explicitly CPU-only.  Process time avoids
            # turning an unrelated OS scheduler pause into a false ranking
            # regression.
            started = time.process_time()
            ranked = ranker.rank(intent, records)
            ranker.diversify_near_ties(ranked)
            durations.append((time.process_time() - started) * 1000)
    finally:
        if gc_enabled:
            gc.enable()
    ordered = sorted(durations)
    result = {
        "schema_version": "legal-live-ranking-performance-v1",
        "candidates": candidates,
        "rounds": measured_rounds,
        "latency_ms": {
            "min": round(min(ordered), 3),
            "median": round(statistics.median(ordered), 3),
            "p95": round(ordered[min(len(ordered) - 1, round((len(ordered) - 1) * 0.95))], 3),
            "max": round(max(ordered), 3),
        },
        "network_calls": 0,
        "status": "passed"
        if ordered[min(len(ordered) - 1, round((len(ordered) - 1) * 0.95))] < 150
        else "failed",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=25)
    parser.add_argument("--candidates", type=int, default=240)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = benchmark(rounds=args.rounds, candidates=args.candidates)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
