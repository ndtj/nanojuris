"""Offline comparisons for provider filter and pagination evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any


def _key(record: Any) -> str:
    if isinstance(record, Mapping):
        for name in ("id", "source_id", "case_number", "registry_number", "number"):
            value = record.get(name)
            if value not in (None, ""):
                return f"{name}:{value}"
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
    return "hash:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _keys(records: Iterable[Any]) -> set[str]:
    return {_key(record) for record in records}


def compare_pages(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    """Compare two captured pages without treating an error as an empty page."""

    left_records = list(left.get("results") or [])
    right_records = list(right.get("results") or [])
    left_keys = _keys(left_records)
    right_keys = _keys(right_records)
    left_status = str(left.get("access_status") or left.get("status") or "unknown")
    right_status = str(right.get("access_status") or right.get("status") or "unknown")
    overlap = left_keys & right_keys
    return {
        "left_count": len(left_records),
        "right_count": len(right_records),
        "overlap_count": len(overlap),
        "overlap_keys": sorted(overlap),
        "duplicate_page": bool(overlap),
        "provider_match": left.get("source") == right.get("source"),
        "status_match": left_status == right_status,
        "left_status": left_status,
        "right_status": right_status,
        "total_known": left.get("total_known") is True and right.get("total_known") is True,
        "total_match": left.get("total") == right.get("total")
        if left.get("total_known") is True and right.get("total_known") is True
        else None,
    }


def compare_filter_runs(baseline: Mapping[str, Any], variant: Mapping[str, Any]) -> dict[str, Any]:
    """Report the observable effect of a filter from replayed page envelopes."""

    base_status = str(baseline.get("access_status") or baseline.get("status") or "unknown")
    variant_status = str(variant.get("access_status") or variant.get("status") or "unknown")
    base_keys = _keys(baseline.get("results") or [])
    variant_keys = _keys(variant.get("results") or [])
    blocked = any(
        status in {"blocked", "access_control_required", "login_required", "rate_limited"}
        for status in (base_status, variant_status)
    )
    return {
        "baseline_count": len(base_keys),
        "variant_count": len(variant_keys),
        "retained_count": len(base_keys & variant_keys),
        "removed_count": len(base_keys - variant_keys),
        "added_count": len(variant_keys - base_keys),
        "effect_observed": bool(base_keys - variant_keys) and not blocked,
        "status": "blocked" if blocked else "comparable",
        "baseline_status": base_status,
        "variant_status": variant_status,
        "filter": variant.get("filter") or variant.get("filters") or {},
    }


__all__ = ["compare_filter_runs", "compare_pages"]
