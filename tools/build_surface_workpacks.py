"""Materialize one conservative workpack for every national surface."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "coverage" / "surface-state-registry-20260902.json"
OUTPUT_DIR = (
    ROOT / "specs" / "changes" / "0091-national-coverage-gold-handoff" / "surface-workpacks"
)
MANIFEST = OUTPUT_DIR / "manifest.json"

GATES = (
    "official_source",
    "degree_contract",
    "runtime",
    "fixtures",
    "pagination_filters",
    "bounded_live",
    "canonical_quality",
    "federation",
)


def build(root: Path = ROOT) -> dict[str, Any]:
    registry_path = root / REGISTRY.relative_to(ROOT)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    surfaces = list(registry.get("surfaces", []))
    packs = []
    for surface in surfaces:
        packs.append(_pack(surface))
    return {
        "schema_version": "surface-workpacks-v1",
        "generated_from": str(registry_path.relative_to(root)).replace("\\", "/"),
        "surface_count": len(packs),
        "required_surface_count": sum(1 for item in packs if item["required"]),
        "complete_gate_count": sum(
            all(gate["status"] == "passed" for gate in item["gates"]) for item in packs
        ),
        "workpacks": packs,
    }


def _pack(surface: dict[str, Any]) -> dict[str, Any]:
    source_id = str(surface.get("provider") or surface.get("diagnostic_provider") or "")
    evidence = [str(item) for item in surface.get("evidence_ids", [])]
    gates = _gates(surface, source_id, evidence)
    safe_name = _safe_name(str(surface.get("surface_id", "surface")))
    return {
        "surface_id": str(surface.get("surface_id", "")),
        "authority": surface.get("authority"),
        "branch": surface.get("branch"),
        "degree": surface.get("degree"),
        "instance": surface.get("instance"),
        "collection": surface.get("collection"),
        "scope": surface.get("scope"),
        "required": bool(surface.get("required", False)),
        "provider": source_id or None,
        "lifecycle": surface.get("lifecycle", "unknown"),
        "contract_status": surface.get("contract_status", "unknown"),
        "live_status": surface.get("live_status", "unknown"),
        "federation_status": surface.get("federation_status", "unknown"),
        "legal_status": surface.get("legal_status", "unknown"),
        "document_capability": surface.get("document_capability", {}),
        "evidence_ids": evidence,
        "next_action": _next_action(surface, source_id),
        "gates": gates,
        "relative_path": f"{safe_name}.md",
    }


def _gates(surface: dict[str, Any], source_id: str, evidence: list[str]) -> list[dict[str, Any]]:
    lifecycle = str(surface.get("lifecycle", "unknown"))
    contract = str(surface.get("contract_status", "unknown"))
    live = str(surface.get("live_status", "unknown"))
    federation = str(surface.get("federation_status", "unknown"))
    blocked_live = {
        "access_control_required",
        "access_controlled",
        "blocked_access",
        "blocked_transport",
        "source_unavailable",
    }
    fixture_status = "passed" if source_id and source_id in _fixture_sources() else "pending"
    return [
        {"gate": "official_source", "status": "passed" if evidence else "pending"},
        {
            "gate": "degree_contract",
            "status": "passed" if contract == "live_validated" else "pending",
        },
        {"gate": "runtime", "status": "passed" if lifecycle == "implemented" else "pending"},
        {"gate": "fixtures", "status": fixture_status},
        {
            "gate": "pagination_filters",
            "status": "passed" if contract == "live_validated" else "pending",
        },
        {
            "gate": "bounded_live",
            "status": "passed"
            if live == "valid"
            else ("blocked" if live in blocked_live else "pending"),
        },
        {
            "gate": "canonical_quality",
            "status": "passed"
            if contract == "live_validated" and surface.get("maturity") not in {None, "unknown"}
            else "pending",
        },
        {
            "gate": "federation",
            "status": "passed"
            if federation == "enabled"
            else ("blocked" if federation == "blocked" else "pending"),
        },
    ]


def _fixture_sources() -> set[str]:
    path = ROOT / "docs" / "coverage" / "fixture-completeness-20260908.json"
    if not path.is_file():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(row.get("source"))
        for row in payload.get("providers", [])
        if row.get("source") and row.get("complete")
    }


def _next_action(surface: dict[str, Any], source_id: str) -> str:
    live = str(surface.get("live_status", "unknown"))
    if live in {"access_control_required", "access_controlled", "blocked_transport"}:
        return "record official access state once and evaluate an authorized alternative"
    if not source_id:
        return "discover and contract one official public route for this surface"
    if str(surface.get("contract_status")) != "live_validated":
        return "close the degree-specific contract with bounded public evidence"
    if str(surface.get("federation_status")) != "enabled":
        return "run opt-in federation smoke and preserve legal status separately"
    return "maintain TTL smoke and monitor schema drift"


def _safe_name(surface_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", surface_id).strip("_") or "surface"


def render(pack: dict[str, Any]) -> str:
    lines = [
        f"# Surface workpack — `{pack['surface_id']}`",
        "",
        "Generated from the canonical surface registry. This file records state; "
        "it does not promote a provider.",
        "",
        "## Identity",
        "",
        "```yaml",
        f"surface_id: {pack['surface_id']}",
        f"authority: {pack['authority']}",
        f"branch: {pack['branch']}",
        f"degree: {pack['degree']}",
        f"instance: {pack['instance']}",
        f"collection: {pack['collection']}",
        f"provider: {pack['provider'] or 'null'}",
        f"required: {str(pack['required']).lower()}",
        f"lifecycle: {pack['lifecycle']}",
        f"contract_status: {pack['contract_status']}",
        f"live_status: {pack['live_status']}",
        f"federation_status: {pack['federation_status']}",
        f"legal_status: {pack['legal_status']}",
        "```",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- `{item}`" for item in pack["evidence_ids"] or ["none recorded"])
    lines.extend(["", "## Gates", "", "| Gate | State |", "| --- | --- |"])
    lines.extend(f"| `{gate['gate']}` | `{gate['status']}` |" for gate in pack["gates"])
    lines.extend(
        [
            "",
            "## Document capability",
            "",
            "```json",
            json.dumps(pack["document_capability"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Next action",
            "",
            pack["next_action"],
            "",
            "External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and "
            "schema drift are never treated as empty results.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    payload = build(root)
    output_dir = root / OUTPUT_DIR.relative_to(ROOT)
    if args.write:
        output_dir.mkdir(parents=True, exist_ok=True)
        for pack in payload["workpacks"]:
            (output_dir / pack["relative_path"]).write_text(render(pack), encoding="utf-8")
        (output_dir / "manifest.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(
        json.dumps(
            {
                key: payload[key]
                for key in ("surface_count", "required_surface_count", "complete_gate_count")
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
