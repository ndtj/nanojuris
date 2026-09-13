"""Privacy-preserving, opt-in telemetry facts for live search evaluation."""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from nanojuris.governance import DEFAULT_OPERATIONAL_POLICY

TELEMETRY_RETENTION_DAYS = DEFAULT_OPERATIONAL_POLICY.telemetry_retention_days


def fingerprint_query(query: str, *, secret: bytes) -> str:
    """Return an opaque HMAC fingerprint; never persist the query text."""

    if not secret:
        raise ValueError("telemetry secret must not be empty")
    return hmac.new(secret, query.strip().encode("utf-8"), hashlib.sha256).hexdigest()


def build_search_event(
    *,
    query: str,
    secret: bytes,
    ranking_version: str,
    provider: str,
    position: int | None = None,
    canonical_id: str | None = None,
    action: str = "impression",
    latency_ms: float | None = None,
    source_status: str | None = None,
) -> dict[str, Any]:
    """Build the bounded analytics projection used by shadow evaluation."""

    if position is not None and position < 1:
        raise ValueError("position must be positive")
    if latency_ms is not None and latency_ms < 0:
        raise ValueError("latency_ms must be non-negative")
    return {
        "schema_version": "search-telemetry-v1",
        "query_hmac_sha256": fingerprint_query(query, secret=secret),
        "ranking_version": ranking_version,
        "provider": provider,
        "position": position,
        "canonical_id": canonical_id,
        "action": action,
        "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
        "source_status": source_status,
        "raw_query": None,
    }


__all__ = ["TELEMETRY_RETENTION_DAYS", "build_search_event", "fingerprint_query"]
