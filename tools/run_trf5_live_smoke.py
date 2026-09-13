"""Bounded live verification of the public TRF5 search pagination and detail."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nanojuris import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.trf5_jurisprudencia import Trf5JurisprudenciaProvider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "trf5-live-20260907-cycle45.json"


def _page_summary(page: Any) -> dict[str, Any]:
    return {
        "http_status": page.source_trace.http_status if page.source_trace else None,
        "page": page.page,
        "page_size": page.page_size,
        "returned": len(page.results),
        "total_known": page.total_known,
        "ids": [result.id for result in page.results],
        "case_numbers": [result.number for result in page.results],
        "has_summary": all(bool(result.summary) for result in page.results),
    }


def run(output: Path) -> dict[str, Any]:
    provider = Trf5JurisprudenciaProvider(NanoJurisConfig(timeout=30, rate_limit_interval=0))
    query = JurisprudenceQuery(text="dano moral", page_size=1)
    rows: dict[str, Any] = {}
    try:
        first = provider.search(query)
        rows["page_1"] = _page_summary(first)
        if first.results:
            document_id = first.results[0].raw.get("id_documento")
            if document_id:
                document = provider.get_document(str(document_id))
                rows["detail"] = {
                    "status": "valid",
                    "byte_size": document.byte_size,
                    "content_type": document.content_type,
                    "sha256": document.sha256,
                    "has_text": bool(document.text),
                }
            else:
                rows["detail"] = {"status": "not_observed"}
        else:
            rows["detail"] = {"status": "not_observed"}
        second = provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=1))
        rows["page_2"] = _page_summary(second)
        ids_1 = set(rows["page_1"]["ids"])
        ids_2 = set(rows["page_2"]["ids"])
        rows["pagination"] = {
            "status": "valid" if ids_1.isdisjoint(ids_2) else "overlap",
            "disjoint_ids": ids_1.isdisjoint(ids_2),
        }
    except Exception as exc:  # noqa: BLE001 - report a classified bounded failure
        rows["error"] = {"type": type(exc).__name__, "message": str(exc)[:240]}

    report = {
        "schema_version": "trf5-live-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live_bounded",
        "source": "trf5_jurisprudencia",
        "source_id": "trf5_jurisprudencia",
        "surface": "search",
        "classification": "valid"
        if all(rows.get(key, {}).get("http_status") == 200 for key in ("page_1", "page_2"))
        else "unknown",
        "status": "valid"
        if all(rows.get(key, {}).get("http_status") == 200 for key in ("page_1", "page_2"))
        else "source_unavailable",
        "access_status": "public" if "error" not in rows else "source_unavailable",
        "retrieval_status": "ok" if "error" not in rows else "error",
        "extraction_status": "complete"
        if rows.get("detail", {}).get("has_text") is True
        else "partial",
        "query": {"text": "dano moral", "page_size": 1},
        "limits": {"pages": 2, "documents": 1, "bodies_persisted": False},
        "record_count_observed": rows.get("page_1", {}).get("returned", 0),
        "reported_total": rows.get("page_1", {}).get("total_known"),
        "pagination_mode": "page",
        "http_status": rows.get("page_1", {}).get("http_status"),
        "content_type": rows.get("detail", {}).get("content_type"),
        "response_bytes": rows.get("detail", {}).get("byte_size"),
        "sha256": rows.get("detail", {}).get("sha256"),
        "content_sha256": rows.get("detail", {}).get("sha256"),
        "full_text_status": "document_available"
        if rows.get("detail", {}).get("has_text") is True
        else "unknown",
        "observations": rows,
        "summary": {
            "search_valid": all(
                rows.get(key, {}).get("http_status") == 200 for key in ("page_1", "page_2")
            ),
            "pagination_valid": rows.get("pagination", {}).get("status") == "valid",
            "detail_valid": rows.get("detail", {}).get("status") == "valid",
            "errors": 1 if "error" in rows else 0,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.output.resolve())["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
