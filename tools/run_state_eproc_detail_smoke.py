"""Bounded live search/detail smoke for state eproc jurisprudence.

The command requests one second-degree record from TJRJ and TJSC, then follows
the public document route for that observed identifier. Only hashes and
metadata are persisted; response bodies, cookies and tokens are discarded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nanojuris import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjrj_eproc_jurisprudencia import TjrjEprocJurisprudenciaProvider
from nanojuris.providers.tjsc_eproc_jurisprudencia import TjscEprocJurisprudenciaProvider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "state-eproc-detail-live-20260906.json"


def _row(provider: Any, query: JurisprudenceQuery) -> dict[str, Any]:
    row: dict[str, Any] = {"provider": provider.name, "search": {}, "detail": {}}
    try:
        page = provider.search(query)
        result = page.results[0] if page.results else None
        row["search"] = {
            "http_status": page.source_trace.http_status if page.source_trace else None,
            "returned": len(page.results),
            "total_known": page.total_known,
            "degree_values": sorted(
                {str(item.degree) for item in page.results if item.degree is not None}
            ),
            "id": result.id if result is not None else None,
        }
        if result is None:
            row["detail"] = {"status": "not_observed"}
            return row
        try:
            document = provider.get_document(result.id)
            text = document.text or ""
            row["detail"] = {
                "status": "valid" if text.strip() else "empty",
                "http_status": document.source_trace.http_status if document.source_trace else None,
                "content_type": document.content_type,
                "byte_size": document.byte_size,
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "has_text": bool(text.strip()),
            }
        except Exception as exc:  # noqa: BLE001 - classified live evidence
            row["detail"] = {"status": "error", "error_type": type(exc).__name__}
    except Exception as exc:  # noqa: BLE001 - classified live evidence
        row["search"] = {"status": "error", "error_type": type(exc).__name__}
        row["detail"] = {"status": "not_observed"}
    return row


def run(output: Path) -> dict[str, Any]:
    query = JurisprudenceQuery(text="responsabilidade civil", degree="second", page_size=1)
    config = NanoJurisConfig(timeout=30, rate_limit_interval=0)
    rows = [
        _row(TjrjEprocJurisprudenciaProvider(config), query),
        _row(TjscEprocJurisprudenciaProvider(config), query),
    ]
    report = {
        "schema_version": "state-eproc-detail-live-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "bounded_public_http",
        "query": query.to_dict(),
        "limits": {"providers": 2, "documents_per_provider": 1, "bodies_persisted": False},
        "providers": rows,
        "summary": {
            "search_valid": sum(row["search"].get("http_status") == 200 for row in rows),
            "detail_valid": sum(row["detail"].get("status") == "valid" for row in rows),
            "detail_empty": sum(row["detail"].get("status") == "empty" for row in rows),
            "detail_errors": sum(row["detail"].get("status") == "error" for row in rows),
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
