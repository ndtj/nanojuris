"""Run a bounded live smoke for the public BNP/Pangea precedent API."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nanojuris import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.bnp_pangea import BnpPangeaProvider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "bnp-pangea-live-20260905-cycle59.json"


def _page_summary(page: Any) -> dict[str, Any]:
    trace = page.source_trace
    return {
        "http_status": trace.http_status if trace else None,
        "content_type": trace.content_type if trace else None,
        "response_bytes": trace.response_bytes if trace else None,
        "page": page.page,
        "page_size": page.page_size,
        "returned": len(page.results),
        "total": page.total,
        "total_known": page.total_known,
        "ids": [result.id for result in page.results],
        "types": sorted({result.type for result in page.results}),
        "courts": sorted({result.court for result in page.results}),
        "has_thesis": all(bool(result.thesis) for result in page.results),
        "access_status": getattr(page.access_status, "value", page.access_status),
        "extraction_status": getattr(page.extraction_status, "value", page.extraction_status),
    }


def run(output: Path) -> dict[str, Any]:
    provider = BnpPangeaProvider(NanoJurisConfig(timeout=20, rate_limit_interval=0))
    query = JurisprudenceQuery(
        text="responsabilidade civil",
        courts=["STF", "STJ"],
        types=["RG", "RR"],
        page_size=2,
    )
    observations: dict[str, Any] = {}
    try:
        first = provider.search(query)
        observations["page_1"] = _page_summary(first)
        second = provider.search(
            JurisprudenceQuery(
                text=query.text,
                courts=query.courts,
                types=query.types,
                page=2,
                page_size=query.page_size,
            )
        )
        observations["page_2"] = _page_summary(second)
        ids_1 = set(observations["page_1"]["ids"])
        ids_2 = set(observations["page_2"]["ids"])
        observations["pagination"] = {
            "status": "valid" if ids_1.isdisjoint(ids_2) else "overlap",
            "disjoint_ids": ids_1.isdisjoint(ids_2),
        }
    except Exception as exc:  # noqa: BLE001 - classify bounded live failures
        observations["error"] = {"type": type(exc).__name__, "message": str(exc)[:240]}

    page_1 = observations.get("page_1", {})
    report = {
        "schema_version": "bnp-pangea-live-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live_bounded",
        "source": "bnp_pangea",
        "source_id": "bnp_pangea",
        "surface": "search",
        "classification": "valid"
        if page_1.get("http_status") == 200 and page_1.get("returned", 0) > 0
        else "unknown",
        "http_status": page_1.get("http_status"),
        "content_type": page_1.get("content_type"),
        "record_count_observed": page_1.get("returned", 0),
        "reported_total": page_1.get("total"),
        "pagination_mode": "page",
        "provider": "bnp_pangea",
        "query": {
            "text": query.text,
            "courts": query.courts,
            "types": query.types,
            "page_size": query.page_size,
        },
        "limits": {"pages": 2, "bodies_persisted": False},
        "observations": observations,
        "summary": {
            "search_valid": page_1.get("http_status") == 200 and page_1.get("returned", 0) > 0,
            "pagination_valid": observations.get("pagination", {}).get("status") == "valid",
            "total_known": page_1.get("total_known") is True,
            "errors": 1 if "error" in observations else 0,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = run(args.output.resolve())
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
