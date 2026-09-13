"""Build the canonical state registry for national jurisprudence surfaces.

The provider catalog describes adapters, while the degree matrix describes
expected tribunal/collection surfaces.  This projection joins both views and
keeps lifecycle, contract, live, federation, legal and document state
independent.  It is generated data: no status is inferred from a route name
alone and no legal approval is assumed.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
# The 2026-09-01 matrix is the canonical generated projection.  The registry
# filename retains the 20260902 compatibility name used by existing consumers,
# but must read the latest matrix so its summary cannot drift from coverage.
DEFAULT_MATRIX = ROOT / "docs" / "topology" / "degree-coverage-matrix-20260901.json"
DEFAULT_CATALOG = ROOT / "docs" / "registry" / "provider-catalog.full.json"
DEFAULT_APPROVALS = ROOT / "docs" / "operations" / "provider-promotion-approvals-20260905.json"
DEFAULT_PROMOTION_MANIFEST = (
    ROOT / "docs" / "operations" / "technical-promotion-manifest-20260905.json"
)
DEFAULT_OUTPUT = ROOT / "docs" / "coverage" / "surface-state-registry-20260902.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "docs" / "coverage" / "surface-state-registry-20260902.md"

LEGAL_PENDING = "pending_human_review"
OPERATOR_APPROVED = "operator_approved"

# A diagnostic/catalog provider may have proved that an official route exists
# while still being unable to satisfy the degree-specific adapter contract.
# Keep that evidence visible on the required gap without pretending the
# diagnostic provider implements the surface.
DIAGNOSTIC_PROVIDERS: dict[tuple[str, str, str], str] = {
    ("TJMA", "CJSG", "second"): "tjma_jurisconsult",
}


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _catalog_entries(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(entry["source_id"]): entry
        for entry in payload.get("entries", [])
        if isinstance(entry, dict) and entry.get("source_id")
    }


def _provider_lifecycle(surface: dict[str, Any], provider: dict[str, Any] | None) -> str:
    if provider:
        return str(provider.get("lifecycle") or surface.get("status") or "unknown")
    return str(surface.get("status") or "unknown")


def _contract_status(surface: dict[str, Any], provider: dict[str, Any] | None) -> str:
    status = str(surface.get("status") or "unknown")
    if status == "implemented":
        if provider and provider.get("live_status") in {"valid", "implemented"}:
            return "live_validated"
        return "implemented_local"
    if status == "blocked_access":
        return "blocked_access"
    if status == "blocked_transport":
        return "blocked_transport"
    if status == "source_unavailable":
        return "source_unavailable"
    if status == "out_of_scope":
        return "out_of_scope"
    if status == "pending_contract":
        return "pending_contract"
    if status == "live_not_federated":
        return "live_validated"
    if status == "candidate":
        return "candidate"
    return "unknown"


def _live_status(provider: dict[str, Any] | None) -> str:
    if not provider:
        return "not_observed"
    value = provider.get("live_status")
    return str(value) if value else "not_observed"


def _federation_status(
    surface: dict[str, Any],
    provider: dict[str, Any] | None,
    live_status: str,
    promotion_mode: str | None,
) -> str:
    if str(surface.get("status")) in {
        "blocked_access",
        "blocked_transport",
        "source_unavailable",
    }:
        return "blocked"
    if not provider or not (provider.get("interfaces") or {}).get("unified_search"):
        return "not_enabled"
    if live_status in {"blocked_access", "blocked_transport", "access_controlled"}:
        return "blocked"
    # The generated promotion manifest is the technical source of truth for
    # federation.  A capability declaration alone is not enough: providers
    # that are merely opt-in, incomplete, or blocked must remain visible in
    # diagnostics without being called by the default federated route.
    if promotion_mode != "enabled":
        return "not_enabled"
    # A mixed JURISPRUDENCIA surface can be federated through its provider
    # even when no degree-specific CJPG/CJSG binding is proven.  Keep degree
    # surfaces gated by ``queryable`` so a generic adapter never inflates
    # national first/second-instance coverage.
    if not surface.get("queryable") and surface.get("collection") != "JURISPRUDENCIA":
        return "not_enabled"
    return "enabled"


def _document_capability(provider: dict[str, Any] | None) -> dict[str, Any]:
    contract = (provider or {}).get("document_contract") or {}
    if not contract:
        return {
            "status": "unknown",
            "supports_full_text": False,
            "full_text_access": "unknown",
            "formats": [],
            "document_types": [],
        }
    return {
        "status": "declared",
        "supports_full_text": bool(contract.get("supports_full_text", False)),
        "full_text_access": contract.get("full_text_access") or "unknown",
        "formats": list(contract.get("content_formats") or []),
        "document_types": list(contract.get("document_types") or []),
    }


def _row(
    surface: dict[str, Any],
    providers: dict[str, dict[str, Any]],
    approved_sources: set[str],
    technically_ready_sources: set[str],
    operator_accepts_all_technically_ready: bool,
    promotion_modes: dict[str, str],
) -> dict[str, Any]:
    provider_id = surface.get("provider")
    provider = providers.get(str(provider_id)) if provider_id else None
    diagnostic_id = DIAGNOSTIC_PROVIDERS.get(
        (str(surface.get("authority")), str(surface.get("collection")), str(surface.get("degree")))
    )
    diagnostic_provider = providers.get(diagnostic_id) if diagnostic_id else None
    status_provider = provider or diagnostic_provider
    live_status = _live_status(status_provider)
    live_validation = (status_provider or {}).get("live_validation") or {}
    interfaces = (provider or {}).get("interfaces") or {}
    evidence = list(surface.get("evidence_ids") or [])
    if provider_id:
        evidence.append(f"provider-catalog:{provider_id}")
    if diagnostic_id and diagnostic_provider:
        evidence.append(f"provider-catalog:{diagnostic_id}")
        diagnostic_evidence = (diagnostic_provider.get("live_validation") or {}).get("evidence")
        if diagnostic_evidence:
            evidence.append(str(diagnostic_evidence))
    return {
        "surface_id": surface["surface_id"],
        "authority": surface["authority"],
        "branch": surface["branch"],
        "degree": surface["degree"],
        "instance": "first" if surface["degree"] == "first" else surface["degree"],
        "collection": surface["collection"],
        "scope": surface.get("scope", "tribunal"),
        "required": bool(surface.get("required", False)),
        "provider": provider_id,
        "diagnostic_provider": diagnostic_id,
        "lifecycle": _provider_lifecycle(surface, provider),
        "maturity": (provider or {}).get("maturity_tier") or "unknown",
        "live_status": live_status,
        "last_live_check": live_validation.get("date"),
        "contract_status": _contract_status(surface, provider),
        "federation_status": _federation_status(
            surface, provider, live_status, promotion_modes.get(str(provider_id))
        ),
        "legal_status": OPERATOR_APPROVED
        if str(provider_id) in approved_sources
        or (
            operator_accepts_all_technically_ready and str(provider_id) in technically_ready_sources
        )
        else LEGAL_PENDING,
        "document_capability": _document_capability(provider),
        "queryable_direct": bool(surface.get("queryable", False)),
        "interfaces": {
            "unified_search": bool(interfaces.get("unified_search", False)),
            "cli": bool(interfaces.get("cli", False)),
            "mcp": bool(interfaces.get("mcp", False)),
            "studio": bool(interfaces.get("studio", False)),
        },
        "document_types": list(surface.get("document_types") or []),
        "evidence_ids": sorted(set(evidence)),
        "notes": surface.get("notes") or "",
    }


def build(
    *,
    matrix_path: Path = DEFAULT_MATRIX,
    catalog_path: Path = DEFAULT_CATALOG,
    approvals_path: Path = DEFAULT_APPROVALS,
    promotion_manifest_path: Path = DEFAULT_PROMOTION_MANIFEST,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Return a deterministic registry joined from matrix and catalog."""

    matrix = _read(matrix_path)
    catalog = _catalog_entries(_read(catalog_path))
    approvals = _read(approvals_path) if approvals_path.exists() else {}
    approved_sources = {
        str(source)
        for source in approvals.get("approved_sources", [])
        if isinstance(source, str) and source.strip()
    }
    promotion_manifest = _read(promotion_manifest_path) if promotion_manifest_path.exists() else {}
    promotion_policy = promotion_manifest.get("policy") or {}
    technically_ready_sources = {
        str(source)
        for source in (promotion_manifest.get("summary") or {}).get("technical_ready_sources", [])
        if isinstance(source, str) and source.strip()
    }
    operator_accepts_all = bool(promotion_policy.get("operator_accepts_all_technically_ready"))
    promotion_modes = {
        str(item.get("source")): str(item.get("mode"))
        for item in promotion_manifest.get("decisions", [])
        if isinstance(item, dict) and item.get("source")
    }
    surfaces = [
        _row(
            surface,
            catalog,
            approved_sources,
            technically_ready_sources,
            operator_accepts_all,
            promotion_modes,
        )
        for surface in matrix.get("surfaces", [])
    ]
    surfaces.sort(key=lambda item: item["surface_id"])
    if len({item["surface_id"] for item in surfaces}) != len(surfaces):
        raise ValueError("surface_id duplicado no registro de estados")

    divergences: list[dict[str, str]] = []
    for item in surfaces:
        provider_id = str(item.get("provider") or "")
        if provider_id and provider_id not in catalog:
            divergences.append(
                {
                    "surface_id": str(item["surface_id"]),
                    "kind": "provider_missing_from_catalog",
                    "provider": provider_id,
                }
            )
        if item["provider"] and item["diagnostic_provider"]:
            divergences.append(
                {
                    "surface_id": str(item["surface_id"]),
                    "kind": "runtime_and_diagnostic_provider_both_present",
                    "provider": provider_id,
                    "diagnostic_provider": str(item["diagnostic_provider"]),
                }
            )
        if item["diagnostic_provider"] and not item["provider"]:
            divergences.append(
                {
                    "surface_id": str(item["surface_id"]),
                    "kind": "diagnostic_evidence_without_runtime_binding",
                    "diagnostic_provider": str(item["diagnostic_provider"]),
                }
            )

    required = [item for item in surfaces if item["required"]]
    return {
        "schema_version": "surface-state-registry-v1",
        "generated_at": generated_at or matrix.get("generated_at") or "unknown",
        "source_artifacts": [
            str(matrix_path.relative_to(ROOT)).replace("\\", "/"),
            str(catalog_path.relative_to(ROOT)).replace("\\", "/"),
            str(approvals_path.relative_to(ROOT)).replace("\\", "/"),
            str(promotion_manifest_path.relative_to(ROOT)).replace("\\", "/"),
        ],
        "summary": {
            "surface_count": len(surfaces),
            "required_surface_count": len(required),
            "by_lifecycle": dict(sorted(Counter(item["lifecycle"] for item in surfaces).items())),
            "by_contract_status": dict(
                sorted(Counter(item["contract_status"] for item in surfaces).items())
            ),
            "by_live_status": dict(
                sorted(Counter(item["live_status"] for item in surfaces).items())
            ),
            "by_federation_status": dict(
                sorted(Counter(item["federation_status"] for item in surfaces).items())
            ),
            "by_legal_status": dict(
                sorted(Counter(item["legal_status"] for item in surfaces).items())
            ),
            "cjpg": {
                "implemented": sum(
                    item["collection"] == "CJPG" and item["contract_status"] == "live_validated"
                    for item in required
                ),
                "expected": sum(item["collection"] == "CJPG" for item in required),
            },
            "cjsg": {
                "implemented": sum(
                    item["collection"] == "CJSG" and item["contract_status"] == "live_validated"
                    for item in required
                ),
                "expected": sum(item["collection"] == "CJSG" for item in required),
            },
            "divergence_count": len(divergences),
            "scope_note": (
                "Estados de contrato, live, federação e legalidade são independentes. "
                "Aprovação legal nunca é inferida do catálogo ou de uma chamada pública."
            ),
        },
        "divergences": divergences,
        "surfaces": surfaces,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Registro canônico de estados das superfícies",
        "",
        f"Geração: `{payload['generated_at']}`; superfícies: **{summary['surface_count']}**; "
        f"obrigatórias: **{summary['required_surface_count']}**.",
        "",
        "Este artefato é a fonte de verdade para o estado por superfície. "
        "`lifecycle`, `contract_status`, `live_status`, `federation_status` e "
        "`legal_status` não são equivalentes.",
        "",
        "## CJPG/CJSG",
        "",
        "| Coleção | Live-validado | Esperado |",
        "|---|---:|---:|",
        f"| CJPG | {summary['cjpg']['implemented']} | {summary['cjpg']['expected']} |",
        f"| CJSG | {summary['cjsg']['implemented']} | {summary['cjsg']['expected']} |",
        "",
        "## Contagens por estado",
        "",
        "| Dimensão | Contagens |",
        "|---|---|",
    ]
    for key in (
        "by_lifecycle",
        "by_contract_status",
        "by_live_status",
        "by_federation_status",
        "by_legal_status",
    ):
        values = ", ".join(f"`{name}`={count}" for name, count in summary[key].items())
        lines.append(f"| `{key}` | {values} |")
    lines.extend(
        [
            "",
            "## Superfícies",
            "",
            "| Superfície | Autoridade | Grau | Coleção | Provider | Contrato | "
            "Live | Federação | Legal |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for item in payload["surfaces"]:
        lines.append(
            f"| `{item['surface_id']}` | `{item['authority']}` | `{item['degree']}` | "
            f"`{item['collection']}` | "
            f"{('`' + item['provider'] + '`') if item['provider'] else '—'} | "
            f"`{item['contract_status']}` | `{item['live_status']}` | "
            f"`{item['federation_status']}` | `{item['legal_status']}` |"
        )
    lines.extend(["", summary["scope_note"], ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    matrix = args.matrix if args.matrix.is_absolute() else ROOT / args.matrix
    catalog = args.catalog if args.catalog.is_absolute() else ROOT / args.catalog
    output = args.output if args.output.is_absolute() else ROOT / args.output
    markdown_output = (
        args.markdown_output if args.markdown_output.is_absolute() else ROOT / args.markdown_output
    )
    payload = build(matrix_path=matrix, catalog_path=catalog, generated_at=args.generated_at)
    write_json(output, payload)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "surface_count": payload["summary"]["surface_count"],
                "required_surface_count": payload["summary"]["required_surface_count"],
                "cjpg": payload["summary"]["cjpg"],
                "cjsg": payload["summary"]["cjsg"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
