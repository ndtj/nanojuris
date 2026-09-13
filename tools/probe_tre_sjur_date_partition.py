"""Probe bounded monthly SJUR/TRE partitions without persisting response bodies.

This tool exercises the same public, opt-in adapter used by callers.  It is
deliberately serial and bounded: no credentials, cookies, challenge tokens,
proxies, retries or alternate transports are used.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tse_sjur_jurisprudencia import (
    TRE_STATES,
    TreSjurFirstDegreeProvider,
    TreSjurJurisprudenciaProvider,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "tre-sjur-date-partition-uf-sweep-live.json"


def probe(
    *,
    start: str,
    end: str,
    text: str,
    document_type: str,
    degree: str,
    timeout: float,
    interval: float,
    authorities: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    query = JurisprudenceQuery(
        text=text,
        document_type=document_type,
        judgment_date_from=start,
        judgment_date_to=end,
        page_size=10,
    )
    selected_authorities = authorities or tuple(f"TRE-{state}" for state in TRE_STATES)
    results: list[dict[str, Any]] = []
    for index, authority in enumerate(selected_authorities):
        started = time.perf_counter()
        record: dict[str, Any] = {"authority": authority}
        provider_class = (
            TreSjurFirstDegreeProvider if degree == "first" else TreSjurJurisprudenciaProvider
        )
        provider = provider_class(
            NanoJurisConfig(rate_limit_interval=0, timeout=timeout),
            tribunal=authority,
        )
        try:
            page = provider.search_partitioned(query)
            record.update(
                {
                    "http_status": page.source_trace.http_status if page.source_trace else None,
                    "total": page.total,
                    "returned": len(page.results),
                    "total_known": page.total_known,
                    "complete": page.is_complete,
                    "status": (
                        "complete"
                        if page.total_known is True and page.is_complete is True
                        else "partial"
                    ),
                }
            )
        except Exception as exc:  # noqa: BLE001 - redacted probe classification
            record.update(
                {
                    "status": type(exc).__name__,
                    "message": str(exc)[:160],
                }
            )
        record["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
        results.append(record)
        if index < len(selected_authorities) - 1:
            time.sleep(max(interval, 0.0))
    complete = sum(item.get("status") == "complete" for item in results)
    return {
        "schema_version": "tre-sjur-date-partition-uf-sweep-v1",
        "provider": ("tre_sjur_first_degree" if degree == "first" else "tre_sjur_jurisprudencia"),
        "collection": "SJUR",
        "branch": "electoral",
        "degree": degree,
        "checked_at": datetime.now(timezone.utc).date().isoformat(),
        "classification": (
            "bounded_date_partition_complete" if complete == len(results) else "partial"
        ),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "request": {
            "text": text,
            "document_type": document_type,
            "degree": degree,
            "judgment_date_from": start,
            "judgment_date_to": end,
            "partitions": "monthly",
        },
        "checked": len(results),
        "complete": complete,
        "response_bodies_persisted": False,
        "body_persisted": False,
        "credentials_used": False,
        "bypass_attempted": False,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--end", default="2025-01-31")
    parser.add_argument("--text", default="direito")
    parser.add_argument("--document-type", default="acordao")
    parser.add_argument("--degree", choices=("first", "second"), default="second")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = probe(
        start=args.start,
        end=args.end,
        text=args.text,
        document_type=args.document_type,
        degree=args.degree,
        timeout=args.timeout,
        interval=args.interval,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"checked": payload["checked"], "complete": payload["complete"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
