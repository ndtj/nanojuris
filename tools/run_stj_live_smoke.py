"""Run a bounded, redacted smoke for the public STJ surfaces."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from nanojuris import NanoJurisClient, NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, SourceUnavailableError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "stj-live-20260908-cycle74.json"


def _host(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return urlparse(value).netloc or None


def _search(client: NanoJurisClient, source: str, query: str) -> dict[str, object]:
    started = time.perf_counter()
    try:
        page = client.search(query, source=source, page_size=1)
    except AccessControlRequiredError as exc:
        return {
            "source": source,
            "classification": "access_blocked",
            "error_type": type(exc).__name__,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "raw_content_persisted": False,
        }
    except SourceUnavailableError as exc:
        return {
            "source": source,
            "classification": "source_unavailable",
            "error_type": type(exc).__name__,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "raw_content_persisted": False,
        }
    results = list(page.results)
    document_hosts = {
        host for result in results for host in [_host(result.raw.get("document_url"))] if host
    }
    return {
        "source": source,
        "classification": "success_with_results" if results else "unconfirmed_empty",
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "returned": len(results),
        "total_state": getattr(page, "total_state", None),
        "document_hosts": sorted(document_hosts),
        "source_trace_present": page.source_trace is not None,
        "raw_content_persisted": False,
    }


def _open_data(client: NanoJurisClient) -> dict[str, object]:
    started = time.perf_counter()
    source = "stj_dados_abertos_jurisprudencia"
    try:
        datasets = client.list_source_datasets(source=source, query="jurisprudencia", rows=20)
        first = datasets[0] if datasets else None
        plan = (
            client.plan_source_sync(
                source=source,
                dataset_id=str(first["name"]),
                format="JSON",
            )
            if first
            else None
        )
        return {
            "source": source,
            "classification": "success_with_results" if datasets else "unconfirmed_empty",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "dataset_count": len(datasets),
            "sync_download": bool(plan and plan.get("download")),
            "raw_content_persisted": False,
        }
    except SourceUnavailableError as exc:
        return {
            "source": source,
            "classification": "source_unavailable",
            "error_type": type(exc).__name__,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "raw_content_persisted": False,
        }


def build() -> dict[str, object]:
    client = NanoJurisClient(config=NanoJurisConfig(timeout=30, rate_limit_interval=0.5))
    checks = [
        _search(client, "stj_informativo", "infanticidio"),
        _search(client, "stj_scon", "responsabilidade civil"),
        _open_data(client),
    ]
    return {
        "schema_version": "stj-live-smoke-v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "bounded": True,
        "credentials_used": False,
        "bypass_used": False,
        "raw_content_persisted": False,
        "checks": checks,
        "summary": {
            "success": sum(item["classification"] == "success_with_results" for item in checks),
            "blocked_or_unavailable": sum(
                item["classification"] in {"access_blocked", "source_unavailable"}
                for item in checks
            ),
            "errors": sum("error_type" in item for item in checks),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
