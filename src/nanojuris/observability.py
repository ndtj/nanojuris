"""Opt-in live contract probes and honest SLI summaries.

This module is an operator boundary: it never runs during import, search or
CI.  Callers must provide an explicit allowlist and a bounded timeout.  The
result is metadata only; response bodies are never persisted by this helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from nanojuris.errors import safe_error_message


@dataclass(frozen=True, slots=True)
class ProbePolicy:
    """Allowlist and budget for one bounded provider validation run."""

    allowed_sources: tuple[str, ...]
    timeout_seconds: float = 60.0
    max_workers: int = 3
    page_size: int = 1
    query_text: str = "responsabilidade civil"

    def __post_init__(self) -> None:
        normalized = tuple(
            dict.fromkeys(item.strip() for item in self.allowed_sources if item.strip())
        )
        object.__setattr__(self, "allowed_sources", normalized)
        if self.timeout_seconds <= 0 or self.max_workers < 1 or self.page_size < 1:
            raise ValueError("probe budget values must be positive")
        if not self.query_text.strip():
            raise ValueError("query_text must not be empty")


def run_allowlisted_probe(client: Any, policy: ProbePolicy) -> dict[str, Any]:
    """Run a bounded probe and return redacted reports for the operator."""

    result = client.validate_sources(
        sources=list(policy.allowed_sources),
        text=policy.query_text,
        page_size=policy.page_size,
        timeout=policy.timeout_seconds,
        max_workers=policy.max_workers,
    )
    reports = result.get("reports", []) if isinstance(result, dict) else []
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "bounded_allowlisted_live_probe",
        "policy": {
            "allowed_sources": list(policy.allowed_sources),
            "timeout_seconds": policy.timeout_seconds,
            "max_workers": policy.max_workers,
            "page_size": policy.page_size,
            "query_text_sha256": _sha256(policy.query_text),
        },
        "reports": [_redact_report(report) for report in reports if isinstance(report, dict)],
        "summary": summarize_slis(reports),
        "complete": bool(result.get("complete", False)) if isinstance(result, dict) else False,
    }


def summarize_slis(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate access/latency/schema/result SLIs without overclaiming uptime."""

    statuses: dict[str, int] = {}
    latencies: list[float] = []
    for report in reports:
        status = str(report.get("status", "unknown"))
        statuses[status] = statuses.get(status, 0) + 1
        elapsed = report.get("elapsed_ms")
        if isinstance(elapsed, int | float) and elapsed >= 0:
            latencies.append(float(elapsed))
    valid = statuses.get("valid", 0)
    empty = statuses.get("empty", 0)
    observed = sum(statuses.values())
    return {
        "observed_sources": observed,
        "status_counts": dict(sorted(statuses.items())),
        "contract_pass_rate": ((valid + empty) / observed if observed else None),
        "latency_ms_p50": _percentile(latencies, 0.5),
        "latency_ms_p95": _percentile(latencies, 0.95),
        "availability_claim": "point_in_time_only",
    }


def _redact_report(report: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "source",
        "status",
        "checked_at",
        "elapsed_ms",
        "returned",
        "reported_total",
        "pagination_mode",
        "completeness",
        "completeness_reason",
        "source_url",
        "endpoint",
        "http_status",
        "access_status",
        "retrieval_status",
        "extraction_status",
        "requested_page_size",
        "effective_page_size",
        "content_type",
        "content_sha256",
        "response_bytes",
        "full_text_status",
        "checks",
        "failed_checks",
        "error_type",
    }
    result = {key: report[key] for key in allowed if key in report}
    if "message" in report:
        result["message"] = safe_error_message(str(report["message"]))
    return result


def _sha256(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * quantile)))
    return round(ordered[index], 2)


__all__ = ["ProbePolicy", "run_allowlisted_probe", "summarize_slis"]
