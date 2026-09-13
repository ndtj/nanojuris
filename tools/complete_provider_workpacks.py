"""Apply a bounded, evidence-based disposition to every provider work pack.

This command closes the *processing* loop; it does not claim that every source
is implemented or healthy.  Sources that lack a contract, fixtures, or a
reproducible live observation are explicitly deferred with a review condition.
Technically-ready sources from the promotion manifest are accepted with their
residual limitations.  No network call, federation mutation, or deployment is
performed here.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = str(ROOT / "src")
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(1, str(ROOT))

from tools.build_provider_sdd_workpacks import (  # noqa: E402
    _read_json,
    _write_json,
    build,
)

TERMINAL_STATES = {
    "accepted",
    "accepted_with_limitations",
    "rejected",
    "deferred_with_review",
    "out_of_scope",
}

MANIFEST_PATH = ROOT / "docs" / "operations" / "technical-promotion-manifest-20260905.json"
OWNER = "nanojuris-provider-maintainers"
REVIEW_AFTER = (date.today() + timedelta(days=30)).isoformat()


def _manifest_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("source", "")): row for row in payload.get("decisions", [])}


def _health(decision: dict[str, Any], entry: dict[str, Any]) -> str:
    access = str(decision.get("access_status", "unknown"))
    live = str(decision.get("live_status", entry.get("live_status", "unknown")))
    if access == "blocked_access" or live in {"blocked", "blocked_access", "access_controlled"}:
        return "access_controlled"
    if access == "blocked_transport" or live in {"blocked_transport", "tls_verification_failed"}:
        return "tls_error"
    if access == "source_unavailable" or live in {"source_unavailable", "unavailable"}:
        return "unavailable"
    if live in {"valid", "valid_data", "implemented"}:
        return "valid"
    if live in {"empty_confirmed", "empty_unconfirmed"}:
        return "degraded"
    return "not_checked"


def _resume_when(decision: dict[str, Any], entry: dict[str, Any]) -> str:
    reasons = {str(value) for value in decision.get("reasons", [])}
    lifecycle = str(entry.get("implementation_status", entry.get("lifecycle", "unknown")))
    if "blocked_access" in reasons:
        return "reexecute a bounded public request after the source removes access control"
    if "blocked_transport" in reasons:
        return "reexecute a bounded request after the official transport/TLS path is healthy"
    if "source_unavailable" in reasons:
        return "recheck when the official source is available again"
    if lifecycle in {"none", "candidate"} or "contract_gate_failed" in reasons:
        return (
            "approve an official contract, implement the adapter, and add "
            "success/empty/failure fixtures"
        )
    if "reproducible_fixture_missing" in reasons:
        return "add sanitized versioned success, explicit-empty, and failure/schema fixtures"
    if "live_validation_missing" in reasons:
        return "run one bounded live check against the documented public route"
    if "quality_gate_failed" in reasons:
        return "close the quality gate and rerun the promotion manifest"
    return "rerun the provider completion command after new source evidence"


def classify_provider(
    entry: dict[str, Any], decision: dict[str, Any], *, review_after: str = REVIEW_AFTER
) -> dict[str, Any]:
    """Return a deterministic terminal decision without changing the input."""

    mode = str(decision.get("mode", "opt_in"))
    reasons = [str(value) for value in decision.get("reasons", []) if value]
    health = _health(decision, entry)
    source = str(entry.get("source_id", decision.get("source", "unknown")))
    if mode == "enabled" and bool(decision.get("technical_gate")):
        disposition = "accepted_with_limitations"
        status = "ready_for_review"
        phase = "review"
        resume = "rerun the promotion manifest after any contract, parser, or schema change"
        reason = "technical gates passed; residual limitations remain recorded in the work pack"
        review = None
    else:
        disposition = "deferred_with_review"
        status = "waiting_evidence"
        phase = "research" if entry.get("implementation_status") in {"none", "family"} else "review"
        resume = _resume_when(decision, entry)
        reason = "; ".join(reasons) or "technical promotion gate did not pass"
        review = review_after

    evidence = [
        "docs/operations/technical-promotion-manifest-20260905.json",
        "docs/registry/provider-catalog.full.json",
        "specs/changes/0035-provider-completion-autopilot/provider-baseline.json",
    ]
    blocking = {
        "kind": "completion_decision",
        "source": source,
        "disposition": disposition,
        "reason": reason,
        "resume_when": resume,
    }
    return {
        "status": status,
        "phase": phase,
        "attempts": 1,
        "owner": OWNER,
        "last_checkpoint": {
            "command": "python tools/complete_provider_workpacks.py --write",
            "outcome": disposition,
        },
        "blocking_conditions": [blocking] if disposition == "deferred_with_review" else [],
        "evidence": evidence,
        "operational_health": health,
        "disposition": disposition,
        "review_after": review,
        "resume_when": resume,
        "completion_reason": reason,
    }


def apply_completion(root: Path, output_dir: Path, *, write: bool) -> dict[str, Any]:
    """Refresh the generated inputs and apply terminal dispositions idempotently."""

    # Always derive from the current catalog and preserve existing evidence via
    # the normal generator.  This also makes the command safe to resume.
    build(root, output_dir)
    baseline = _read_json(output_dir / "provider-baseline.json", {"providers": []})
    state = _read_json(output_dir / "execution-state.json", {"providers": {}})
    manifest = _read_json(root / "docs" / "operations" / MANIFEST_PATH.name, {"decisions": []})
    entries = {
        str(row.get("source_id", "")): row
        for row in _read_json(
            root / "docs" / "registry" / "provider-catalog.full.json", {"entries": []}
        ).get("entries", [])
    }
    decisions = _manifest_map(manifest)
    providers = state.setdefault("providers", {})
    applied: dict[str, dict[str, Any]] = {}
    for row in baseline.get("providers", []):
        source = str(row.get("source_id", ""))
        entry = entries.get(source, row)
        decision = decisions.get(source, {})
        current = dict(providers.get(source, {}))
        result = classify_provider(entry, decision)
        # Keep the generator's fingerprint and topology fields authoritative.
        prior_evidence = [str(value) for value in current.get("evidence", [])]
        result["evidence"] = list(dict.fromkeys(prior_evidence + result["evidence"]))
        prior_blocking = current.get("blocking_conditions", [])
        if isinstance(prior_blocking, list) and prior_blocking:
            historical_blocking = [
                item
                for item in prior_blocking
                if not (
                    isinstance(item, dict)
                    and item.get("kind") == "completion_decision"
                    and item.get("source") == source
                )
            ]
            result["blocking_conditions"] = historical_blocking + result["blocking_conditions"]
        for key, value in result.items():
            current[key] = value
        current["evidence_fingerprint"] = row.get(
            "evidence_fingerprint", current.get("evidence_fingerprint")
        )
        current["priority"] = row.get("priority", current.get("priority"))
        current["target_tier"] = row.get("target_tier", current.get("target_tier"))
        current["topology_collection_ids"] = row.get(
            "topology_collection_ids", current.get("topology_collection_ids", [])
        )
        current["workpack"] = row.get("workpack", current.get("workpack"))
        providers[source] = current
        applied[source] = {
            "disposition": result["disposition"],
            "status": result["status"],
            "operational_health": result["operational_health"],
        }

    counts = Counter(item["disposition"] for item in applied.values())
    summary = {
        "providers": len(applied),
        "dispositions": dict(sorted(counts.items())),
        "terminal": sum(counts.values()),
        "mode": "offline_evidence_review",
        "network": "not_used",
        "review_after": REVIEW_AFTER,
    }
    state["updated_at"] = date.today().isoformat()
    state["completion_run"] = summary
    if write:
        _write_json(output_dir / "execution-state.json", state)
        # Run the generator once more so work packs and the summary reflect the
        # state atomically and retain the normal generated-artifact format.
        build(root, output_dir)
    return {"summary": summary, "providers": applied}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "specs" / "changes" / "0035-provider-completion-autopilot",
    )
    parser.add_argument(
        "--write", action="store_true", help="persist state and regenerated work packs"
    )
    args = parser.parse_args()
    root = args.root.resolve()
    output = (
        args.output_dir.resolve()
        if args.output_dir.is_absolute()
        else (root / args.output_dir).resolve()
    )
    result = apply_completion(root, output, write=args.write)
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
