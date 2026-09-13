"""Evaluate provider promotion gates and emit a deterministic manifest.

The manifest is deliberately a *decision artifact*, not a runtime mutation.
Technical readiness is computed from the catalog.  Local operation may opt in
to every technically-ready source through an explicit operator decision, while
blocked or incomplete sources remain out of federation.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = str(ROOT / "src")
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)

from nanojuris.governance import (  # noqa: E402
    ProviderPromotionEvidence,
    RolloutMode,
    evaluate_provider_promotion,
)

DEFAULT_CATALOG = ROOT / "docs" / "registry" / "provider-catalog.full.json"
DEFAULT_LEGAL_MANIFEST = ROOT / "docs" / "operations" / "provider-promotion-approvals-20260905.json"
DEFAULT_OUTPUT = ROOT / "docs" / "operations" / "technical-promotion-manifest-20260905.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "operations" / "technical-promotion-manifest-20260905.md"
ACCEPT_ALL_TECHNICAL = "__all_technically_ready__"


def _load_legal_allowlist(path: Path | None) -> set[str]:
    """Read the operator decision file, returning no approvals by default.

    Accepted shapes are ``{"approved_sources": [...]}`` or a bare JSON list.
    An absent file is intentional and means that every human approval gate is
    pending.  The historical function name is retained for compatibility.
    """

    if path is None or not path.exists():
        return set()
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        sources = value
    elif isinstance(value, dict):
        sources = value.get("approved_sources", [])
        if value.get("operator_accepts_all_technically_ready") is True:
            # The operator explicitly authorized local/federated use of every
            # source that passes the independent technical gates.  Keep this
            # marker separate from source ids so a future provider cannot be
            # enabled merely by appearing in the catalog.
            sources = [*sources, ACCEPT_ALL_TECHNICAL]
    else:
        raise ValueError("legal manifest must be a JSON list or object")
    if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
        raise ValueError("approved_sources must be a list of source ids")
    return {item.strip() for item in sources if item.strip()}


def _contract_valid(entry: dict[str, Any]) -> bool:
    contract = entry.get("source_contract")
    if not isinstance(contract, dict):
        return False
    evidence = contract.get("evidence")
    if not isinstance(evidence, dict):
        return False
    endpoints = evidence.get("endpoints")
    level = contract.get("contract_level")
    return isinstance(endpoints, list) and bool(endpoints) and isinstance(level, int) and level >= 4


def _fixtures_complete(entry: dict[str, Any]) -> bool:
    documentation = entry.get("documentation", {})
    quality = entry.get("quality_contract", {})
    refs = documentation.get("fixture_references", 0)
    readiness = documentation.get("readiness")
    flags = quality.get("quality_flags", [])
    # Three fixtures are the minimum reproducible envelope: success, empty,
    # and an explicit failure/schema-drift case.
    return isinstance(refs, int) and refs >= 3 and readiness not in {None, "missing"} and not flags


def _quality_passed(entry: dict[str, Any]) -> bool:
    score = entry.get("maturity_score", {}).get("total")
    tier = entry.get("maturity_tier")
    quality_flags = entry.get("quality_contract", {}).get("quality_flags", [])
    return (
        isinstance(score, (int, float))
        and score >= 70
        and tier not in {"blocked", "family", "mapped"}
        and not quality_flags
    )


def _access_status(entry: dict[str, Any]) -> str:
    live = entry.get("live_status")
    if live in {"blocked_access", "access_controlled", "access_control_required"}:
        return "blocked_access"
    if live in {"blocked_transport", "transport_blocked"}:
        return "blocked_transport"
    if live in {"source_unavailable", "unavailable"}:
        return "source_unavailable"
    # An authoritative empty response proves that the public route was
    # reachable and parsed. It must not be confused with a transport failure
    # or make a technically complete provider look unvalidated.
    if live in {"valid", "implemented", "reachable_empty_data"}:
        return "public"
    return "unknown"


def build_manifest(
    catalog: dict[str, Any], legal_approved: set[str] | None = None
) -> dict[str, Any]:
    """Build promotion decisions for every catalog entry."""

    approved = legal_approved or set()
    decisions: list[dict[str, Any]] = []
    for entry in sorted(catalog.get("entries", []), key=lambda item: item.get("source_id", "")):
        source = str(entry.get("source_id", ""))
        lifecycle = entry.get("lifecycle")
        contract_valid = lifecycle == "implemented" and _contract_valid(entry)
        live_validated = entry.get("live_status") in {"valid", "reachable_empty_data"}
        fixtures_complete = lifecycle == "implemented" and _fixtures_complete(entry)
        quality_passed = lifecycle == "implemented" and _quality_passed(entry)
        access_status = _access_status(entry)
        evidence = ProviderPromotionEvidence(
            source=source,
            contract_valid=contract_valid,
            live_validated=live_validated,
            fixtures_complete=fixtures_complete,
            quality_gate_passed=quality_passed,
            legal_approved=(source in approved or ACCEPT_ALL_TECHNICAL in approved),
            access_status=access_status,
            # A technically complete specialized source may still be
            # deliberately opt-in (for example a qualified-precedent
            # catalog).  Never turn a declared non-default interface into a
            # default federated source merely because its other gates pass.
            requested_mode=(
                RolloutMode.ENABLED
                if bool(entry.get("interfaces", {}).get("unified_search"))
                else RolloutMode.OPT_IN
            ),
        )
        decision = evaluate_provider_promotion(evidence)
        row = decision.to_dict()
        row.update(
            {
                "lifecycle": lifecycle,
                "live_status": entry.get("live_status"),
                "contract_valid": contract_valid,
                "live_validated": live_validated,
                "fixtures_complete": fixtures_complete,
                "quality_gate_passed": quality_passed,
                "legal_approved": (source in approved or ACCEPT_ALL_TECHNICAL in approved),
                # The operator decision is the local/federated rollout gate in
                # this cycle.  Keep ``legal_approved`` above as a compatibility
                # field for older consumers, but expose the actual meaning
                # explicitly so the report cannot imply a legal review occurred.
                "operator_accepted": (source in approved or ACCEPT_ALL_TECHNICAL in approved),
                "access_status": access_status,
                "default_federation_before": bool(
                    entry.get("interfaces", {}).get("unified_search")
                ),
                "opt_in_supported": bool(entry.get("interfaces", {}).get("opt_in_unified_search")),
            }
        )
        decisions.append(row)

    by_mode = Counter(item["mode"] for item in decisions)
    technical_ready = [item["source"] for item in decisions if item["technical_gate"]]
    enabled = [item["source"] for item in decisions if item["mode"] == RolloutMode.ENABLED.value]
    operator_accepted = [
        item["source"] for item in decisions if item["technical_gate"] and item["operator_accepted"]
    ]
    opt_in = [item["source"] for item in decisions if item["mode"] == RolloutMode.OPT_IN.value]
    return {
        "schema_version": "1.0",
        "generated_at": date.today().isoformat(),
        "policy": {
            "technical_promotion_is_automatic": True,
            "default_federation_mutation": False,
            "operator_approval_source": "explicit operator decision",
            "operator_accepts_all_technically_ready": ACCEPT_ALL_TECHNICAL in approved,
            "minimum_contract_level": 4,
            "minimum_fixture_count": 3,
        },
        "summary": {
            "providers": len(decisions),
            "technical_ready": len(technical_ready),
            # This count includes technically accepted opt-in sources.  The
            # actual default federation set remains ``enabled_sources``.
            "enabled_after_operator_approval": len(operator_accepted),
            # Compatibility alias for consumers of the pre-operator-mode
            # manifest schema.
            "enabled_after_explicit_legal_approval": len(enabled),
            "enabled_after_technical_operator_decision": len(operator_accepted),
            "opt_in_sources": opt_in,
            "by_mode": dict(sorted(by_mode.items())),
            "technical_ready_sources": technical_ready,
            "enabled_sources": enabled,
        },
        "decisions": decisions,
    }


def render_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Technical promotion manifest",
        "",
        "Generated by `python tools/build_promotion_manifest.py --write`.",
        "Technical gates are evaluated automatically. The local operator decision",
        "enables every source that passes them; blocked or incomplete sources are",
        "never promoted and the report does not authorize deployment.",
        "",
        f"- Providers: **{manifest['summary']['providers']}**",
        f"- Technical ready: **{manifest['summary']['technical_ready']}**",
        "- Enabled after operator approval: "
        f"**{manifest['summary']['enabled_after_operator_approval']}**",
        "",
        "| Source | Mode | Technical | Operator accepted | Access | Reasons |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in manifest["decisions"]:
        reasons = ", ".join(row["reasons"]) or "—"
        lines.append(
            f"| `{row['source']}` | `{row['mode']}` | "
            f"{str(row['technical_gate']).lower()} | {str(row['operator_accepted']).lower()} | "
            f"`{row['access_status']}` | {reasons} |"
        )
    lines.extend(
        [
            "",
            "A source is enabled only when every technical gate passes. Access",
            "blocks, parser failures and unknown totals remain explicit and are",
            "never converted into empty results.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--legal-manifest", type=Path, default=DEFAULT_LEGAL_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    manifest = build_manifest(catalog, _load_legal_allowlist(args.legal_manifest))
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(manifest), encoding="utf-8")
    else:
        print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
