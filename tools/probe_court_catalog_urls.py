"""Probe tribunal homepages from the local national catalog.

This is an opt-in, bounded diagnostic. It performs one public GET per URL,
does not authenticate, and stores metadata only (never response bodies).
Homepage reachability is not evidence that a jurisprudence route exists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from nanojuris.brazil import COURTS

DEFAULT_OUTPUT = Path("docs/topology/court-catalog-url-probe-20260901.json")
USER_AGENT = "NanoJuris-research/1.0"
TARGET_CODES = {"TJMMG", "TJMSP", "TJMRS"}
UTC = timezone.utc


def _targets() -> list[Any]:
    return [court for court in COURTS if court.code.startswith("TRE") or court.code in TARGET_CODES]


def _classification(status: int | None) -> str:
    if status is None:
        return "transport_error"
    if 200 <= status < 400:
        return "reachable"
    if status in {401, 403, 429}:
        return "access_controlled"
    if status >= 500:
        return "source_unavailable"
    return "unexpected_status"


def probe(*, timeout: float, observed_at: str) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for court in _targets():
        item: dict[str, Any] = {
            "code": court.code,
            "branch": court.branch,
            "state": court.state,
            "url": court.official_url,
            "request_method": "GET",
            "credentials_used": False,
        }
        try:
            response = requests.get(
                court.official_url,
                headers={"User-Agent": USER_AGENT},
                timeout=timeout,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            item.update(
                {
                    "status": None,
                    "classification": "transport_error",
                    "error_type": type(exc).__name__,
                }
            )
        else:
            item.update(
                {
                    "status": response.status_code,
                    "final_url": response.url,
                    "content_type": response.headers.get("content-type"),
                    "response_bytes": len(response.content),
                    "response_sha256": hashlib.sha256(response.content).hexdigest(),
                    "classification": _classification(response.status_code),
                }
            )
        results.append(item)
    return {
        "schema_version": 1,
        "observed_at": observed_at,
        "source": "nanojuris.brazil.COURTS",
        "network_access": "public_bounded_one_request_per_url",
        "targets": len(results),
        "raw_content_persisted": False,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument(
        "--observed-at",
        default=datetime.now(UTC).replace(microsecond=0).isoformat(),
    )
    args = parser.parse_args()
    payload = probe(timeout=args.timeout, observed_at=args.observed_at)
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "targets": payload["targets"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
