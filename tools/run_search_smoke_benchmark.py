"""Run the six bounded ranking smokes without persisting result bodies."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nanojuris import NanoJurisClient, NanoJurisConfig

ROOT = Path(__file__).resolve().parents[1]
QUERIES = (
    "responsabilidade civil administrativa",
    "acórdãos sobre divórcio",
    "dano moral inscrição indevida",
    "servidor público acumulação de cargos",
    "prisão preventiva contemporaneidade",
    "0000000-00.0000.0.00.0000",
)
DEFAULT_OUTPUT = ROOT / "docs" / "benchmarks" / "live-ranking-smoke-20260907.json"


def _safe_status(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return getattr(value, "value", str(value))


def _source_summary(payload: dict[str, Any]) -> dict[str, Any]:
    outcomes = payload.get("source_outcomes_v2", {})
    safe_outcomes: dict[str, Any] = {}
    if isinstance(outcomes, dict):
        for source, outcome in outcomes.items():
            if not isinstance(outcome, dict):
                continue
            safe_outcomes[str(source)] = {
                key: _safe_status(outcome.get(key))
                for key in ("status", "total_state", "pages", "candidate_count", "latency_ms")
                if key in outcome
            }
    return {
        "searched_sources": list(payload.get("searched_sources", [])),
        "source_outcomes": safe_outcomes,
        "source_completeness": payload.get("source_completeness", {}),
        "errors": [
            {key: error.get(key) for key in ("source", "error_type", "message") if key in error}
            for error in payload.get("errors", [])
            if isinstance(error, dict)
        ],
        "total_returned": int(payload.get("total_returned", 0) or 0),
        "ranking_complete": payload.get("ranking_complete"),
        "collection_complete": payload.get("collection_complete"),
    }


def run(*, source: str, output: Path, timeout: float = 8.0) -> dict[str, Any]:
    if not source.strip():
        raise ValueError("source must not be empty")
    config = NanoJurisConfig(
        timeout=timeout,
        unified_timeout=max(12.0, timeout + 4.0),
        unified_max_pages=1,
        unified_max_workers=1,
        rate_limit_interval=0.25,
    )
    client = NanoJurisClient(config=config)
    observations: list[dict[str, Any]] = []
    for query in QUERIES:
        try:
            payload = client.search_many(
                query,
                sources=[source],
                page=1,
                page_size=5,
                mode="selected",
                ranking_version="legal-live-v1",
            )
            observations.append(
                {
                    "query_fingerprint": hashlib.sha256(query.encode()).hexdigest(),
                    **_source_summary(payload),
                }
            )
        except Exception as exc:  # noqa: BLE001 - preserve bounded status
            observations.append(
                {
                    "query_fingerprint": hashlib.sha256(query.encode()).hexdigest(),
                    "errors": [{"source": source, "error_type": type(exc).__name__}],
                    "total_returned": 0,
                    "ranking_complete": False,
                    "collection_complete": False,
                }
            )
    result = {
        "schema_version": "live-ranking-smoke-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live_bounded",
        "source": source,
        "limits": {"pages_per_query": 1, "page_size": 5, "bodies_persisted": False},
        "queries": len(observations),
        "observations": observations,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="cnj_jurisprudencia")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()
    result = run(source=args.source, output=args.output.resolve(), timeout=args.timeout)
    print(json.dumps({"queries": result["queries"], "source": result["source"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
