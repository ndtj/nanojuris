"""Bounded live verification of public eproc search and detail routes.

Only one result per tribunal is requested.  The report stores status, byte
counts and hashes exposed by ``CanonicalDocument``; document bodies are never
written to disk.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nanojuris import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.eproc_jurisprudencia_federal import (
    TnuEprocJurisprudenciaProvider,
    Trf2EprocJurisprudenciaProvider,
    Trf6EprocJurisprudenciaProvider,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "eproc-detail-live-20260905-cycle43.json"


def run(output: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for provider_cls in (
        TnuEprocJurisprudenciaProvider,
        Trf2EprocJurisprudenciaProvider,
        Trf6EprocJurisprudenciaProvider,
    ):
        provider = provider_cls(NanoJurisConfig(timeout=30, rate_limit_interval=0))
        row: dict[str, Any] = {"source": provider.name, "search": {}, "detail": {}}
        try:
            page = provider.search(JurisprudenceQuery(text="aposentadoria", page=1, page_size=1))
            result = page.results[0] if page.results else None
            row["search"] = {
                "http_status": page.source_trace.http_status if page.source_trace else None,
                "returned": len(page.results),
                "total_known": page.total_known,
                "identity": {
                    "authority": result.authority if result is not None else None,
                    "branch": result.branch if result is not None else None,
                    "degree": result.degree if result is not None else None,
                    "instance": result.instance if result is not None else None,
                    "collection": result.collection if result is not None else None,
                },
                "id_jurisprudencia": (
                    result.raw.get("id_jurisprudencia") if result is not None else None
                ),
                "has_summary": bool(result.summary) if result is not None else False,
            }
            if result is not None and result.raw.get("id_jurisprudencia"):
                try:
                    document = provider.get_document(str(result.raw["id_jurisprudencia"]))
                    row["detail"] = {
                        "status": "valid",
                        "byte_size": document.byte_size,
                        "content_type": document.content_type,
                        "sha256": document.sha256,
                        "has_text": bool(document.text),
                    }
                except Exception as exc:  # noqa: BLE001 - report classified failure
                    row["detail"] = {
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "message": str(exc)[:240],
                    }
            else:
                row["detail"] = {"status": "not_observed"}
        except Exception as exc:  # noqa: BLE001 - report classified failure
            row["search"] = {
                "status": "error",
                "error_type": type(exc).__name__,
                "message": str(exc)[:240],
            }
            row["detail"] = {"status": "not_observed"}
        rows.append(row)

    report = {
        "schema_version": "eproc-detail-live-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live_bounded",
        "query": {"text": "aposentadoria", "page": 1, "page_size": 1},
        "limits": {"tribunals": 3, "documents_per_tribunal": 1, "bodies_persisted": False},
        "providers": rows,
        "summary": {
            "search_valid": sum(row["search"].get("http_status") == 200 for row in rows),
            "detail_valid": sum(row["detail"].get("status") == "valid" for row in rows),
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
