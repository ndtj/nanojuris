"""Bounded live verification of the public TST search and detail API."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nanojuris import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tst_jurisprudencia import TstJurisprudenciaProvider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "tst-live-20260907-cycle60.json"


def run(output: Path) -> dict[str, Any]:
    provider = TstJurisprudenciaProvider(NanoJurisConfig(timeout=30, rate_limit_interval=0))
    query = JurisprudenceQuery(text="responsabilidade civil", page_size=1)
    observation: dict[str, Any] = {}
    try:
        page = provider.search(query)
        observation["search"] = {
            "http_status": page.source_trace.http_status if page.source_trace else None,
            "returned": len(page.results),
            "total_known": page.total_known,
            "reported_total": page.total,
            "ids": [item.id for item in page.results],
            "has_summary": all(bool(item.summary) for item in page.results),
        }
        if page.results:
            document = provider.get_document(page.results[0].id)
            observation["detail"] = {
                "status": "valid",
                "byte_size": document.byte_size,
                "content_type": document.content_type,
                "sha256": document.sha256,
                "has_text": bool(document.text),
            }
        else:
            observation["detail"] = {"status": "not_observed"}
    except Exception as exc:  # noqa: BLE001 - bounded diagnostics
        observation["error"] = {"type": type(exc).__name__, "message": str(exc)[:240]}

    search = observation.get("search", {})
    report = {
        "schema_version": "provider-live-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "tst_jurisprudencia",
        "scope": "jurisprudencia",
        "status": "valid" if search.get("http_status") == 200 else "source_unavailable",
        "retrieval_status": "ok" if search.get("http_status") == 200 else "error",
        "extraction_status": "complete" if search.get("returned", 0) else "empty",
        "http_status": search.get("http_status"),
        "record_count_observed": search.get("returned", 0),
        "reported_total": search.get("reported_total"),
        "pagination_mode": "offset",
        "content_type": "application/json",
        "response_bytes": None,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "query": {"text": query.text, "page_size": query.page_size},
        "observation": observation,
        "bodies_persisted": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = run(args.output.resolve())
    print(
        json.dumps(
            {"status": report["status"], "detail": report["observation"].get("detail", {})},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
