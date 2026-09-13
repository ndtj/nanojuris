"""Audit first-degree federation without mutating the rollout set.

The audit proves that a CJPG surface is federated only when its generated
surface state, provider catalog and technical promotion manifest agree.  It
does not promote a provider and never treats a gap, block or unknown state as
an empty result.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SURFACE_PATH = ROOT / "docs/coverage/surface-state-registry-20260902.json"
CATALOG_PATH = ROOT / "docs/registry/provider-catalog.full.json"
MANIFEST_PATH = ROOT / "docs/operations/technical-promotion-manifest-20260905.json"
DEFAULT_OUTPUT = ROOT / "docs/coverage/first-degree-federation-gate-20260908.json"
DEFAULT_MARKDOWN = ROOT / "docs/coverage/first-degree-federation-gate-20260908.md"

VALID_LIVE = {"valid", "valid_data", "reachable_empty_data"}
TERMINAL_FEDERATION = {"enabled", "not_enabled", "blocked", "opt_in"}


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _provider_rows(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("source_id")): row for row in payload.get("entries", [])}


def _manifest_rows(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("source")): row for row in payload.get("decisions", [])}


def audit(
    surface_payload: dict[str, Any],
    catalog_payload: dict[str, Any],
    manifest_payload: dict[str, Any],
) -> dict[str, Any]:
    catalog = _provider_rows(catalog_payload)
    manifest = _manifest_rows(manifest_payload)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []

    for surface in sorted(
        (row for row in surface_payload.get("surfaces", []) if row.get("collection") == "CJPG"),
        key=lambda row: str(row.get("surface_id", "")),
    ):
        provider = surface.get("provider")
        provider_row = catalog.get(str(provider)) if provider else None
        manifest_row = manifest.get(str(provider)) if provider else None
        contract = str(surface.get("contract_status"))
        live = str(surface.get("live_status"))
        federation = str(surface.get("federation_status"))
        technical = bool(manifest_row and manifest_row.get("technical_gate"))
        public = bool(manifest_row and manifest_row.get("access_status") == "public")
        declared = bool(
            provider_row and (provider_row.get("interfaces") or {}).get("unified_search")
        )
        complete = bool(
            provider
            and provider_row
            and manifest_row
            and contract == "live_validated"
            and live in VALID_LIVE
            and federation == "enabled"
            and technical
            and public
            and declared
        )
        state = "federated" if complete else "gap_or_not_ready"
        row = {
            "surface_id": surface.get("surface_id"),
            "authority": surface.get("authority"),
            "provider": provider,
            "contract_status": contract,
            "live_status": live,
            "federation_status": federation,
            "technical_gate": technical,
            "public_access": public,
            "unified_search_declared": declared,
            "state": state,
        }
        rows.append(row)
        if federation == "enabled" and not complete:
            errors.append(f"enabled CJPG surface failed gate: {row['surface_id']}")
        if federation not in TERMINAL_FEDERATION:
            errors.append(f"unknown federation state {federation!r}: {row['surface_id']}")

    federated = [row for row in rows if row["state"] == "federated"]
    gaps = [row for row in rows if row["state"] != "federated"]
    return {
        "schema_version": "first-degree-federation-gate-v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "policy": {
            "mutates_federation": False,
            "unknown_or_blocked_is_not_empty": True,
            "required_gates": [
                "official_source",
                "degree_contract",
                "fixtures",
                "pagination_filters",
                "live_status",
                "quality_gate",
                "public_access",
                "federation_enabled",
            ],
        },
        "summary": {
            "cjpg_surfaces": len(rows),
            "federated": len(federated),
            "not_ready_or_gap": len(gaps),
            "errors": len(errors),
            "federated_authorities": sorted(
                {str(row["authority"]) for row in federated if row.get("authority")}
            ),
        },
        "surfaces": rows,
        "errors": errors,
        "source_files": [
            str(SURFACE_PATH.relative_to(ROOT)),
            str(CATALOG_PATH.relative_to(ROOT)),
            str(MANIFEST_PATH.relative_to(ROOT)),
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Gate de federação CJPG",
        "",
        "Auditoria gerada por `tools/audit_first_degree_federation.py`; não altera o rollout.",
        "",
        f"- Superfícies CJPG: **{summary['cjpg_surfaces']}**",
        f"- Federadas com gates consistentes: **{summary['federated']}**",
        f"- Lacunas ou não prontas: **{summary['not_ready_or_gap']}**",
        f"- Erros de consistência: **{summary['errors']}**",
        "",
        "| Autoridade | Provider | Contrato | Live | Federação | Gates | Estado |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in payload["surfaces"]:
        gates = "ok" if row["state"] == "federated" else "pendente"
        lines.append(
            f"| {row.get('authority') or '—'} | {row.get('provider') or '—'} | "
            f"`{row['contract_status']}` | `{row['live_status']}` | "
            f"`{row['federation_status']}` | `{gates}` | `{row['state']}` |"
        )
    if payload["errors"]:
        lines.extend(["", "## Erros", "", *[f"- {value}" for value in payload["errors"]]])
    lines.extend(
        [
            "",
            "Superfícies sem contrato/live/gates continuam visíveis como lacunas e não são"
            " convertidas em vazio nem promovidas por este relatório.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    payload = audit(_read(SURFACE_PATH), _read(CATALOG_PATH), _read(MANIFEST_PATH))
    if args.write:
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        args.markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0 if not payload["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
