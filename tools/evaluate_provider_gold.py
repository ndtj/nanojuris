"""Evaluate the five engineering/provider-gold axes from the capability ledger.

This evaluator is intentionally read-only.  It distinguishes engineering
completeness from live health and federation rollout, and never changes a
provider registration or legal decision.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "coverage" / "provider-capability-ledger.json"
OUTPUT = ROOT / "docs" / "quality" / "provider-gold-evaluation.json"
OUTPUT_MD = ROOT / "docs" / "quality" / "provider-gold-evaluation.md"


def _parse_date(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _task(row: dict[str, Any], name: str) -> bool:
    return any(
        item.get("id") == name and item.get("status") == "complete"
        for item in row.get("workpack", {}).get("tasks", [])
    )


def evaluate(
    ledger: dict[str, Any], *, as_of: datetime | None = None, max_age_days: int = 30
) -> dict[str, Any]:
    now = as_of or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max_age_days)
    rows: list[dict[str, Any]] = []
    for provider in ledger.get("providers", []):
        live_at = _parse_date(provider.get("live", {}).get("checked_at"))
        freshness = (
            "fresh"
            if live_at is not None and live_at >= cutoff
            else "expired"
            if live_at
            else "missing"
        )
        filters = provider.get("contract", {}).get("filters", {})
        field_classification = provider.get("data", {}).get("field_classification", {})
        # A missing classification is different from an empty one.  The
        # evaluator accepts the compact fixture shape used by older ledgers,
        # but a real provider must explicitly close every observed field.
        # Keep the concrete unresolved names in the report.  A boolean-only
        # gate made it impossible to tell whether a provider was blocked by a
        # single missing filter or by an incomplete field inventory.  Names
        # are taken from the ledger (which is the source of truth), sorted for
        # deterministic reports and safe diffing in CI.
        unverified_filters = sorted(
            str(value) for value in filters.get("unverified", []) if str(value).strip()
        )
        unverified_fields = sorted(
            str(name)
            for name, value in field_classification.items()
            if value in {"unverified", "unknown", ""}
        )
        filter_complete = "unverified" in filters and not unverified_filters
        fields_complete = bool(field_classification) and not unverified_fields
        compact_data_contract = not field_classification and bool(
            provider.get("data", {}).get("extracted_fields")
        )
        axes = {
            "contract": _task(provider, "runtime_contract") and filter_complete,
            "data": bool(provider.get("data", {}).get("canonical_records"))
            and (fields_complete or compact_data_contract),
            "document": _task(provider, "documents"),
            "live": provider.get("live", {}).get("status") in {"valid", "valid_data"}
            and freshness == "fresh",
            "federation": bool(provider.get("contract", {}).get("supports_unified_search")),
        }
        axis_reasons = {
            "contract": "complete"
            if axes["contract"]
            else (
                "unverified_filters:" + ",".join(unverified_filters)
                if unverified_filters
                else "runtime/filter evidence incomplete"
            ),
            "data": "complete"
            if axes["data"]
            else (
                "unverified_fields:" + ",".join(unverified_fields)
                if unverified_fields
                else "canonical field classification incomplete"
            ),
            "document": "terminal" if axes["document"] else "document task pending",
            "live": "fresh valid check"
            if axes["live"]
            else f"status={provider.get('live', {}).get('status')}, freshness={freshness}",
            "federation": "unified search declared" if axes["federation"] else "not declared",
        }
        engineering = all(axes[name] for name in ("contract", "data", "document"))
        rows.append(
            {
                "source_id": provider.get("source_id"),
                "axes": axes,
                "axis_reasons": axis_reasons,
                "engineering_gold": engineering,
                "provider_gold": engineering and axes["live"] and axes["federation"],
                "live_status": provider.get("live", {}).get("status"),
                "freshness": freshness,
                "unverified_filters": unverified_filters,
                "unverified_fields": unverified_fields,
                "provider_gold_blocked_reasons": [
                    reason
                    for reason, enabled in (
                        ("unverified_filters", bool(unverified_filters)),
                        ("unverified_fields", bool(unverified_fields)),
                        ("documents_pending", not axes["document"]),
                        ("live_not_fresh_valid", not axes["live"]),
                        ("federation_not_declared", not axes["federation"]),
                    )
                    if enabled
                ],
                "gaps": provider.get("gaps", []),
            }
        )
    return {
        "schema_version": "provider-gold-evaluation-v1",
        "generated_at": now.replace(microsecond=0).isoformat(),
        "policy": {
            "max_live_age_days": max_age_days,
            "engineering_axes": ["contract", "data", "document"],
            "provider_axes": ["contract", "data", "document", "live", "federation"],
        },
        "summary": {
            "providers": len(rows),
            "engineering_gold": sum(row["engineering_gold"] for row in rows),
            "provider_gold": sum(row["provider_gold"] for row in rows),
            "fresh": sum(row["freshness"] == "fresh" for row in rows),
            "expired": sum(row["freshness"] == "expired" for row in rows),
            "missing_live": sum(row["freshness"] == "missing" for row in rows),
            "blocked_by_unverified_filters": sum(bool(row["unverified_filters"]) for row in rows),
            "blocked_by_unverified_fields": sum(bool(row["unverified_fields"]) for row in rows),
        },
        "providers": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Provider gold evaluation",
        "",
        "Read-only evaluation from the capability ledger; this is not a rollout or legal approval.",
        "",
        "## Summary",
        "",
        *(f"- {key}: {value}" for key, value in report["summary"].items()),
        "",
        "| Provider | Engineering gold | Provider gold | Live freshness | Gaps |",
        "|---|---:|---:|---|---:|",
    ]
    for row in report["providers"]:
        lines.append(
            f"| `{row['source_id']}` | {str(row['engineering_gold']).lower()} | "
            f"{str(row['provider_gold']).lower()} | {row['freshness']} | "
            f"{len(row['gaps'])} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--max-age-days", type=int, default=30)
    args = parser.parse_args()
    report = evaluate(
        json.loads(args.ledger.read_text(encoding="utf-8")), max_age_days=args.max_age_days
    )
    if args.write:
        OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        OUTPUT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
