"""Reconcile provider capabilities into one deterministic, offline ledger.

The ledger joins generated catalog, unified-contract, document, quality and
Juscraper evidence.  It never calls a court and never promotes a provider.
Unknown evidence remains ``unverified`` instead of being inferred as support.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Prefer the checkout's source tree over any globally installed NanoJuris
# package.  This keeps the generator reproducible when invoked directly from
# a clean clone (without requiring callers to set PYTHONPATH).
ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = str(ROOT / "src")
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(1, str(ROOT))

from nanojuris.governance import DEFAULT_OPERATIONAL_POLICY  # noqa: E402

OUTPUT_JSON = ROOT / "docs" / "coverage" / "provider-capability-ledger.json"
OUTPUT_MD = ROOT / "docs" / "coverage" / "provider-capability-ledger.md"

INPUTS = {
    "catalog": "docs/registry/provider-catalog.full.json",
    "unified_contract": "docs/provider-discovery/unified-contract-matrix.json",
    "documents": "docs/coverage/document-capability-inventory.json",
    "quality": "docs/quality/provider-quality.json",
    "juscraper_diff": "docs/provider-discovery/juscraper-semantic-diff-20260906.json",
}

CANONICAL_FIELDS = (
    "source",
    "source_id",
    "authority",
    "branch",
    "degree",
    "instance",
    "collection",
    "document_type",
    "decision_type",
    "case_number",
    "case_class",
    "judging_body",
    "rapporteur",
    "judgment_date",
    "publication_date",
    "source_updated_at",
    "summary",
    "full_text",
    "document_url",
    "raw",
    "source_trace",
)

FILTER_STATUSES = (
    "native",
    "translated",
    "local_postfilter",
    "validated_scope",
    "unsupported",
    "unsupported_by_source",
    "out_of_scope_nanojud",
    "access_blocked",
    "source_unavailable",
    "unverified",
)


def _read(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return "0" * 64


def _map(payload: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    rows = payload.get(key, [])
    return {
        str(row.get("source_id", row.get("source", ""))): row
        for row in rows
        if isinstance(row, dict)
    }


def _filter_summary(row: dict[str, Any]) -> dict[str, Any]:
    classification = row.get("filter_classification") or {}
    counts = Counter(str(value) for value in classification.values())
    result = {
        status: sorted(name for name, value in classification.items() if str(value) == status)
        for status in FILTER_STATUSES
    }
    result["counts"] = {status: counts.get(status, 0) for status in FILTER_STATUSES}
    result["verified"] = sorted(
        name
        for name, value in classification.items()
        if str(value)
        in {
            "native",
            "translated",
            "local_postfilter",
            "validated_scope",
            "unsupported",
            "unsupported_by_source",
            "out_of_scope_nanojud",
            "access_blocked",
            "source_unavailable",
        }
    )
    return result


def _task(task_id: str, complete: bool, reason: str) -> dict[str, str]:
    return {"id": task_id, "status": "complete" if complete else "pending", "reason": reason}


def _wave(entry: dict[str, Any]) -> str:
    role = str(entry.get("coverage_role", ""))
    lifecycle = str(entry.get("implementation_status", ""))
    if lifecycle == "family":
        return "D-family"
    if lifecycle == "none":
        return "D-candidate"
    if role == "primary_textual_jurisprudence":
        return "A-primary"
    if role in {"precedent_context", "specialized_jurisprudence"}:
        return "B-specialized"
    return "C-context"


def build(root: Path = ROOT) -> dict[str, Any]:
    payloads = {name: _read(root, path) for name, path in INPUTS.items()}
    catalog_rows = _map(payloads["catalog"], "entries")
    unified_rows = _map(payloads["unified_contract"], "providers")
    document_rows = _map(payloads["documents"], "providers")
    quality_rows = _map(payloads["quality"], "entries")
    diff_rows = _map(payloads["juscraper_diff"], "records")
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    inputs: dict[str, Any] = {}
    for name, relative in INPUTS.items():
        path = root / relative
        source = payloads[name]
        rows = source.get("entries", source.get("providers", source.get("records", [])))
        inputs[name] = {
            "path": relative,
            "sha256": _sha256(path),
            "record_count": len(rows) if isinstance(rows, list) else 0,
            "generated_at": source.get("generated_at"),
        }

    providers: list[dict[str, Any]] = []
    for source_id in sorted(catalog_rows):
        entry = catalog_rows[source_id]
        unified = unified_rows.get(source_id, {})
        document = document_rows.get(source_id, {})
        quality = quality_rows.get(source_id, {})
        diff = diff_rows.get(source_id, {})
        filters = _filter_summary(unified)
        output_contract = entry.get("output_contract") or {}
        extracted_fields = set(output_contract.get("extracted_fields", []))
        # Classify fields the source actually declares.  A canonical field
        # absent from a provider is not an unverified observation; it is an
        # explicit capability gap reported separately below.  Source-specific
        # fields remain available through ``raw`` rather than being silently
        # discarded.
        field_classification = {
            name: "canonical" if name in CANONICAL_FIELDS else "raw_preserved"
            for name in sorted(extracted_fields)
        }
        unobserved_canonical_fields = sorted(
            name for name in CANONICAL_FIELDS if name not in extracted_fields
        )
        implementation = str(entry.get("implementation_status", "unknown"))
        runtime = implementation == "runtime"
        live_status = str(
            entry.get("live_status", entry.get("live_validation", {}).get("status", "not_recorded"))
        )
        full_text_access = str(
            document.get(
                "full_text_access",
                entry.get("document_contract", {}).get("full_text_access", "unknown"),
            )
        )
        gaps: list[str] = []
        if source_id not in unified_rows:
            gaps.append("missing_unified_contract_row")
        if source_id not in document_rows:
            gaps.append("missing_document_inventory_row")
        if source_id not in quality_rows:
            gaps.append("missing_quality_row")
        if runtime and filters["unverified"]:
            gaps.append(f"unverified_filters:{len(filters['unverified'])}")
        if live_status not in {"valid", "valid_data"}:
            gaps.append(f"live_status:{live_status}")
        if full_text_access in {"unknown", "not_declared"}:
            gaps.append("full_text_capability_unverified")
        for gap in entry.get("known_defects", []) or []:
            gaps.append(f"known_defect:{gap}")
        gaps = list(dict.fromkeys(gaps))
        unified_ok = bool(unified.get("supports_unified_search", False))
        tasks = [
            _task("inventory", True, "catalog row exists"),
            _task(
                "runtime_contract",
                runtime and source_id in unified_rows,
                "runtime and unified evidence" if runtime else "not a runtime provider",
            ),
            _task(
                "filters",
                runtime and not filters["unverified"],
                "all declared common filters classified"
                if not filters["unverified"]
                else f"{len(filters['unverified'])} filters unverified",
            ),
            _task(
                "documents",
                full_text_access not in {"unknown", "not_declared"},
                "document capability terminal"
                if full_text_access not in {"unknown", "not_declared"}
                else "document capability needs evidence",
            ),
            _task("live", live_status in {"valid", "valid_data"}, f"live status={live_status}"),
            _task(
                "federation",
                unified_ok,
                "unified interface declared" if unified_ok else "not enabled/declared",
            ),
            _task(
                "quality",
                not quality.get("critical_gaps") and bool(quality),
                "quality row has no critical gaps" if quality else "quality evidence missing",
            ),
        ]
        providers.append(
            {
                "source_id": source_id,
                "display_name": entry.get("display_name", source_id),
                "classification": {
                    "category": entry.get("category", "unknown"),
                    "coverage_role": entry.get("coverage_role", "unknown"),
                    "lifecycle": entry.get("lifecycle", "unknown"),
                    "implementation_status": implementation,
                    "runtime": runtime,
                },
                "maturity": {
                    "tier": entry.get("maturity_tier"),
                    "score": (entry.get("maturity_score") or {}).get("total"),
                    "quality_tier": quality.get("quality_tier"),
                    "quality_score": quality.get("score"),
                },
                "live": {
                    "status": live_status,
                    "checked_at": (entry.get("live_validation") or {}).get("date")
                    or (entry.get("live_validation") or {}).get("checked_at"),
                    "evidence": (entry.get("live_validation") or {}).get("evidence"),
                    "http_status": (entry.get("live_validation") or {}).get("http_status"),
                },
                "contract": {
                    "supports_unified_search": unified_ok,
                    "pagination_mode": unified.get("pagination_mode"),
                    "completeness_contract": unified.get("completeness_contract"),
                    "filters": filters,
                    "supported_filters": unified.get("supported_filters", []),
                    "canonical_records": unified.get("canonical_records", []),
                },
                "data": {
                    "canonical_records": output_contract.get("canonical_records", []),
                    "extracted_fields": sorted(extracted_fields),
                    "content_formats": output_contract.get("content_formats", []),
                    "field_classification": field_classification,
                    "unobserved_canonical_fields": unobserved_canonical_fields,
                },
                "document": {
                    "supports_full_text": bool(
                        document.get(
                            "supports_full_text",
                            entry.get("document_contract", {}).get("supports_full_text", False),
                        )
                    ),
                    "full_text_access": full_text_access,
                    "document_types": document.get("document_types", []),
                    "detail_modes": document.get("detail_modes", []),
                    "endpoints": document.get("document_endpoints", []),
                    "pipeline_policy": document.get("pipeline_policy", {}),
                },
                "evidence": {
                    "documentation_readiness": (entry.get("documentation") or {}).get("readiness"),
                    "fixture_references": (entry.get("documentation") or {}).get(
                        "fixture_references", 0
                    ),
                    "quality_evidence": quality.get("evidence_summary", []),
                    "juscraper_status": diff.get("status"),
                    "juscraper_evidence": diff.get("evidence", {}),
                },
                "gaps": gaps,
                "workpack": {"wave": _wave(entry), "tasks": tasks},
            }
        )

    summary = {
        "providers": len(providers),
        "runtime": sum(row["classification"]["runtime"] for row in providers),
        "candidates": sum(
            row["classification"]["implementation_status"] == "none" for row in providers
        ),
        "families": sum(
            row["classification"]["implementation_status"] == "family" for row in providers
        ),
        "by_lifecycle": dict(Counter(row["classification"]["lifecycle"] for row in providers)),
        "by_live_status": dict(Counter(row["live"]["status"] for row in providers)),
        "by_wave": dict(Counter(row["workpack"]["wave"] for row in providers)),
        "providers_with_gaps": sum(bool(row["gaps"]) for row in providers),
        "native_filter_declarations": sum(
            row["contract"]["filters"]["counts"]["native"] for row in providers
        ),
        "unverified_filter_declarations": sum(
            row["contract"]["filters"]["counts"]["unverified"] for row in providers
        ),
        "terminal_filter_declarations": sum(
            sum(
                row["contract"]["filters"]["counts"].get(status, 0)
                for status in FILTER_STATUSES
                if status != "unverified"
            )
            for row in providers
        ),
        "full_text_declared": sum(
            row["document"]["full_text_access"] not in {"unknown", "not_declared"}
            for row in providers
        ),
    }
    return {
        "schema_version": "provider-capability-ledger-v1",
        "generated_at": generated_at,
        "mode": "offline_reconciliation",
        "operational_policy": DEFAULT_OPERATIONAL_POLICY.to_dict(),
        "governance": {
            "owner": DEFAULT_OPERATIONAL_POLICY.owner,
            "scope": "core_and_conditional",
            "promotion": "technical_local_manifest_only",
            "release_deploy_production": "blocked",
            "external_contact": "manual_only",
        },
        "decision_record": "docs/coverage/decision-record-20260909.json",
        "inputs": inputs,
        "summary": summary,
        "providers": providers,
    }


def render_markdown(ledger: dict[str, Any]) -> str:
    summary = ledger["summary"]
    lines = [
        "# Provider capability ledger",
        "",
        "Generated offline from current catalog, contracts, document inventory, "
        "quality and Juscraper evidence.",
        "",
        "Operational policy: "
        f"cache TTL {ledger['operational_policy']['live_cache_ttl_seconds']}s; "
        f"telemetry {ledger['operational_policy']['telemetry_retention_days']}d; "
        f"minimum interval "
        f"{ledger['operational_policy']['min_provider_request_interval_seconds']}s; "
        f"bounded pages {ledger['operational_policy']['max_bounded_pages']}; "
        "curated sources opt-in; "
        f"owner {ledger['governance']['owner']}; "
        f"scope {ledger['governance']['scope']}.",
        "",
        "## Summary",
        "",
        *(f"- {key}: {value}" for key, value in summary.items()),
        "",
        "## Provider gaps",
        "",
        "| Provider | Runtime | Live | Filters (native/unsupported/unverified) | "
        "Full text | Gaps |",
        "|---|---:|---|---:|---|---:|",
    ]
    for row in ledger["providers"]:
        counts = row["contract"]["filters"]["counts"]
        lines.append(
            f"| `{row['source_id']}` | {row['classification']['runtime']} | "
            f"{row['live']['status']} | {counts['native']}/"
            f"{counts['unsupported']}/{counts['unverified']} | "
            f"{row['document']['full_text_access']} | {len(row['gaps'])} |"
        )
    lines += [
        "",
        "Unknown and blocked states are preserved; this artifact does not "
        "promote providers or claim national coverage.",
        "",
    ]
    return "\n".join(lines)


def write(ledger: dict[str, Any], root: Path = ROOT) -> None:
    (root / OUTPUT_JSON.relative_to(ROOT)).write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (root / OUTPUT_MD.relative_to(ROOT)).write_text(render_markdown(ledger), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true", help="write JSON and Markdown artifacts")
    parser.add_argument("--check", action="store_true", help="fail when generated JSON differs")
    args = parser.parse_args()
    root = args.root.resolve()
    ledger = build(root)
    if args.check:
        current_path = root / OUTPUT_JSON.relative_to(ROOT)
        current = current_path.read_text(encoding="utf-8") if current_path.is_file() else ""
        # ``generated_at`` is intentionally refreshed when writing, but must
        # not make a deterministic ``--check`` fail when the source inputs did
        # not change.  Compare the generated content while preserving the
        # timestamp already committed in the artifact.
        if current:
            try:
                current_payload = json.loads(current)
            except json.JSONDecodeError:
                current_payload = None
            if isinstance(current_payload, dict) and current_payload.get("generated_at"):
                ledger["generated_at"] = current_payload["generated_at"]
        expected = json.dumps(ledger, ensure_ascii=False, indent=2) + "\n"
        if current != expected:
            raise SystemExit("provider capability ledger is stale; run with --write")
    elif args.write or not (root / OUTPUT_JSON.relative_to(ROOT)).is_file():
        write(ledger, root)
    print(json.dumps(ledger["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
