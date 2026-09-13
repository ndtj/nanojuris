"""Compare two bounded federated windows without persisting result bodies.

This is a read-only rollout guard. Both manifests are queried independently,
then only stable identifiers, counts and sanitized source statuses are written
to the output artifact. It never enables a provider or changes the default
federation set.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nanojuris import NanoJurisClient, NanoJurisConfig, compare_shadow_results

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs" / "operations" / "technical-promotion-manifest-20260905.json"
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "federated-shadow-20260906.json"


def _manifest_sources(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = payload.get("summary", {}).get("enabled_sources", [])
    if not isinstance(sources, list) or not all(isinstance(value, str) for value in sources):
        raise ValueError("manifest summary.enabled_sources must be a list of strings")
    return list(dict.fromkeys(value for value in sources if value))


def _safe_status(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return getattr(value, "value", str(value))


def _redact_completeness(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for source, value in payload.get("source_completeness", {}).items():
        if not isinstance(value, dict):
            continue
        output[str(source)] = {
            key: _safe_status(value.get(key))
            for key in (
                "returned",
                "reported_total",
                "pagination_mode",
                "complete",
                "reason",
                "pages_fetched",
                "invalid_records",
                "error_type",
                "error_message",
            )
            if key in value
        }
    return output


def _window(payload: dict[str, Any]) -> list[Any]:
    # ``collected_results`` is intentionally used only in memory. The output
    # artifact contains identifiers, never these result objects or their raw
    # fields.
    values = payload.get("collected_results", [])
    return list(values) if isinstance(values, list) else []


def _run_window(sources: list[str], *, text: str, page_size: int) -> dict[str, Any]:
    config = NanoJurisConfig(
        timeout=30,
        unified_timeout=90,
        unified_max_pages=1,
        unified_max_workers=max(1, min(16, len(sources))),
        rate_limit_interval=0,
    )
    client = NanoJurisClient(config=config)
    return client.search_many(text, sources=sources, page=1, page_size=page_size)


def build_shadow(
    *,
    baseline_manifest: Path,
    candidate_manifest: Path,
    output: Path,
    text: str,
    page_size: int,
    max_ids: int,
) -> dict[str, Any]:
    baseline_sources = _manifest_sources(baseline_manifest)
    candidate_sources = _manifest_sources(candidate_manifest)
    baseline = _run_window(baseline_sources, text=text, page_size=page_size)
    candidate = _run_window(candidate_sources, text=text, page_size=page_size)
    comparison = compare_shadow_results(_window(baseline), _window(candidate), max_ids=max_ids)
    result = {
        "schema_version": "federated-shadow-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "shadow_bounded",
        "query": {"text": text, "page": 1, "page_size": page_size},
        "limits": {"max_pages_per_source": 1, "max_ids": max_ids, "bodies_persisted": False},
        "baseline_manifest": baseline_manifest.name,
        "candidate_manifest": candidate_manifest.name,
        "baseline_sources": baseline_sources,
        "candidate_sources": candidate_sources,
        "comparison": comparison.to_dict(),
        "baseline": {
            "sources_searched": baseline.get("searched_sources", []),
            "source_completeness": _redact_completeness(baseline),
            "errors": [
                {
                    key: _safe_status(error.get(key))
                    for key in ("source", "error_type", "message")
                    if key in error
                }
                for error in baseline.get("errors", [])
                if isinstance(error, dict)
            ],
            "collection_complete": baseline.get("collection_complete"),
        },
        "candidate": {
            "sources_searched": candidate.get("searched_sources", []),
            "source_completeness": _redact_completeness(candidate),
            "errors": [
                {
                    key: _safe_status(error.get(key))
                    for key in ("source", "error_type", "message")
                    if key in error
                }
                for error in candidate.get("errors", [])
                if isinstance(error, dict)
            ],
            "collection_complete": candidate.get("collection_complete"),
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--candidate-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--text", default="responsabilidade")
    parser.add_argument("--page-size", type=int, default=1)
    parser.add_argument("--max-ids", type=int, default=10_000)
    args = parser.parse_args()
    if args.page_size < 1 or args.page_size > 100:
        parser.error("--page-size must be between 1 and 100")
    if args.max_ids < 1:
        parser.error("--max-ids must be positive")
    result = build_shadow(
        baseline_manifest=args.baseline_manifest.resolve(),
        candidate_manifest=args.candidate_manifest.resolve(),
        output=args.output.resolve(),
        text=args.text,
        page_size=args.page_size,
        max_ids=args.max_ids,
    )
    print(json.dumps(result["comparison"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
