"""Run a bounded live smoke for the public TRF4 eproc jurisprudence portal."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nanojuris import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.trf4_eproc_jurisprudencia import Trf4EprocJurisprudenciaProvider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "trf4-live-20260905-cycle61.json"


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
        "has_summary": all(bool(result.summary) for result in page.results),
    }


def run(output: Path) -> dict[str, Any]:
    provider = Trf4EprocJurisprudenciaProvider(NanoJurisConfig(timeout=20, rate_limit_interval=0))
    query = JurisprudenceQuery(text="responsabilidade civil", page_size=2)
    observations: dict[str, Any] = {}
    try:
        first = provider.search(query)
        observations["page_1"] = _page_summary(first)
        second = provider.search(JurisprudenceQuery(text=query.text, page=2, page_size=2))
        observations["page_2"] = _page_summary(second)
        ids_1 = set(observations["page_1"]["ids"])
        ids_2 = set(observations["page_2"]["ids"])
        observations["pagination"] = {
            "status": "valid" if ids_1.isdisjoint(ids_2) else "overlap",
            "disjoint_ids": ids_1.isdisjoint(ids_2),
        }
        if first.results:
            document = provider.get_document(first.results[0].id)
            observations["detail"] = {
                "status": "valid" if document.text else "empty",
                "http_status": document.source_trace.http_status if document.source_trace else None,
                "content_type": document.content_type,
                "byte_size": document.byte_size,
                "sha256": document.sha256,
                "has_text": bool(document.text),
            }
    except Exception as exc:  # noqa: BLE001 - classify bounded live failures
        observations["error"] = {"type": type(exc).__name__, "message": str(exc)[:240]}

    page_1 = observations.get("page_1", {})
    page_2 = observations.get("page_2", {})
    detail = observations.get("detail", {})
    report = {
        "schema_version": "trf4-live-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live_bounded",
        "source": "trf4_eproc_jurisprudencia",
        "source_id": "trf4_eproc_jurisprudencia",
        "surface": "search",
        "classification": "valid"
        if page_1.get("http_status") == 200 and page_1.get("returned", 0) > 0
        else "unknown",
        "http_status": page_1.get("http_status"),
        "content_type": page_1.get("content_type"),
        "record_count_observed": page_1.get("returned", 0),
        "reported_total": page_1.get("total"),
        "pagination_mode": "page",
        "provider": "trf4_eproc_jurisprudencia",
        "query": {"text": query.text, "page_size": query.page_size},
        "limits": {"pages": 2, "documents": 1, "bodies_persisted": False},
        "observations": observations,
        "summary": {
            "search_valid": page_1.get("http_status") == 200
            and page_1.get("returned", 0) > 0
            and page_2.get("http_status") == 200,
            "pagination_valid": observations.get("pagination", {}).get("status") == "valid",
            "detail_valid": detail.get("status") == "valid" and detail.get("has_text") is True,
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
