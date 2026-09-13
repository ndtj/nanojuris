"""Build an auditable national jurisprudence coverage gap map.

The map is intentionally separate from provider promotion.  It describes every
known surface, including conditional and aggregate surfaces, and states the
missing evidence or gate without turning an unavailable source into an empty
search result.
"""

# Long explanatory strings in the generated report are intentionally readable.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MATRIX = (
    ROOT
    / "specs/changes/0098-national-jurisprudence-gold-coverage/national-source-task-matrix.json"
)
REGISTRY = ROOT / "docs/coverage/surface-state-registry-20260902.json"
CATALOG = ROOT / "docs/registry/provider-catalog.full.json"
QUALITY = ROOT / "docs/quality/provider-quality.json"
OUT_JSON = ROOT / "docs/coverage/national-coverage-gap-map-20260908.json"
OUT_MD = ROOT / "docs/coverage/national-coverage-gap-map-20260908.md"

REQUIRED_FIELDS = (
    "authority",
    "branch",
    "degree",
    "instance",
    "collection",
    "provider",
    "official_entry_point",
    "contract_status",
    "live_status",
    "last_live_check",
    "evidence_ids",
    "document_capability",
    "federation_status",
)

PROVIDER_REQUIRED_FIELDS = (
    "source_url",
    "lifecycle",
    "implementation_status",
    "live_status",
    "evidence_ids",
    "interfaces",
    "document_contract",
)

# The state-court rollup is intentionally explicit.  It is the contractual
# 27-court scope for the CJPG/CJSG coverage promise; TJMs and other branches
# are represented by the full surface list but must not silently enter this
# denominator.
STATE_AUTHORITIES = (
    "TJAC",
    "TJAL",
    "TJAM",
    "TJAP",
    "TJBA",
    "TJCE",
    "TJDFT",
    "TJES",
    "TJGO",
    "TJMA",
    "TJMG",
    "TJMS",
    "TJMT",
    "TJPA",
    "TJPB",
    "TJPE",
    "TJPI",
    "TJPR",
    "TJRJ",
    "TJRN",
    "TJRO",
    "TJRR",
    "TJRS",
    "TJSC",
    "TJSE",
    "TJSP",
    "TJTO",
)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _priority(row: dict[str, Any]) -> str:
    state = str(row.get("current_state"))
    family = str(row.get("family"))
    scope = str(row.get("core_scope"))
    if state in {"blocked_or_unavailable", "contract_pending"} and scope == "core":
        return "P0"
    if state in {"discovery_pending", "live_not_federated"} and scope == "core":
        return "P1"
    if state in {"discovery_pending", "contract_pending"} or family == "conditional":
        return "P2"
    return "P3"


def _workstream(row: dict[str, Any]) -> str:
    state = str(row.get("current_state"))
    if state == "discovery_pending":
        return "official_discovery"
    if state == "contract_pending":
        return "contract_hardening"
    if state == "blocked_or_unavailable":
        return "blocked_recheck_or_official_alternative"
    if state == "live_not_federated":
        return "promotion_gates"
    return "continuous_monitoring"


def _missing_information(row: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_FIELDS:
        value = row.get(field)
        if field == "evidence_ids":
            if not value:
                missing.append(field)
        elif field == "document_capability":
            if not isinstance(value, dict) or value.get("status") in {None, "unknown"}:
                missing.append(field)
        elif value in (None, "", "unknown", "not_observed", "candidate"):
            missing.append(field)
    return missing


def _gate_gaps(row: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    if not row.get("provider"):
        gaps.append("runtime")
    if row.get("contract_status") != "live_validated":
        gaps.append("degree_contract")
    if not row.get("evidence_ids"):
        gaps.append("fixtures_live_evidence")
    if row.get("live_status") != "valid":
        gaps.append("live_status")
    if row.get("federation_status") != "enabled":
        gaps.append("federation")
    document_capability = row.get("document_capability")
    if not isinstance(document_capability, dict) or document_capability.get("status") in {
        None,
        "unknown",
    }:
        gaps.append("document_capability")
    if row.get("legal_status") == "pending_human_review":
        gaps.append("human_legal_review")
    return gaps


def _provider_current_state(entry: dict[str, Any]) -> str:
    """Classify a catalog entry that has no matrix binding yet.

    This is deliberately conservative: a valid live response without an
    explicit unified-search interface is not treated as federated coverage.
    """

    live_status = str(entry.get("live_status") or "")
    implementation = str(entry.get("implementation_status") or "")
    lifecycle = str(entry.get("lifecycle") or "")
    interfaces = entry.get("interfaces") or {}
    if live_status in {
        "access_control_required",
        "blocked",
        "blocked_access",
        "blocked_transport",
        "source_unavailable",
        "timeout",
    }:
        return "blocked_or_unavailable"
    if live_status == "valid" and interfaces.get("unified_search"):
        return "federated_live"
    if live_status == "valid" and implementation == "runtime":
        return "live_not_federated"
    if implementation == "runtime" and lifecycle == "implemented":
        return "contract_pending"
    return "discovery_pending"


def _provider_missing_information(entry: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    identity = entry.get("identity") or {}
    for field in PROVIDER_REQUIRED_FIELDS:
        if field == "source_url":
            value = identity.get("source_url")
        else:
            value = entry.get(field)
        if field == "evidence_ids":
            if not value:
                missing.append(field)
        elif field in {"interfaces", "document_contract"}:
            if not isinstance(value, dict) or not value:
                missing.append(field)
        elif value in (None, "", "unknown", "not_observed"):
            missing.append(field)
    return missing


def _gold_gates(row: dict[str, Any]) -> dict[str, bool]:
    document_capability = row.get("document_capability")
    identity_complete = all(
        row.get(field) not in (None, "", "unknown", "not_observed")
        for field in ("authority", "branch", "degree", "instance", "collection")
    )
    gates = {
        "official_source": bool(row.get("official_entry_point")),
        "degree_contract": row.get("contract_status") == "live_validated",
        "runtime": bool(row.get("provider")),
        "fixtures": row.get("fixture_references", 0) >= 3
        or any("fixture" in str(item).lower() for item in row.get("evidence_ids", [])),
        "live_validated": row.get("live_status") == "valid",
        "identity_and_degree": identity_complete,
        "quality_gate": (
            row.get("quality_gate") == "passed"
            or row.get("maturity") == "gold"
            or (row.get("quality_tier") == "gold" and not row.get("quality_critical_gaps"))
        ),
        "document_capability": isinstance(document_capability, dict)
        and (
            document_capability.get("status") not in (None, "unknown")
            or document_capability.get("full_text_access") not in (None, "unknown")
        ),
        "federation": row.get("federation_status") == "enabled",
    }
    return gates


def _catalog_orphan(
    entry: dict[str, Any], quality_entry: dict[str, Any] | None = None
) -> dict[str, Any]:
    identity = entry.get("identity") or {}
    surface_identity = entry.get("surface_identity") or {}
    quality_entry = quality_entry or {}
    current_state = _provider_current_state(entry)
    row = {
        "row_kind": "catalog_orphan",
        "surface_id": entry.get("surface_id"),
        "authority": surface_identity.get("authority", "unknown"),
        "branch": surface_identity.get("branch", "unknown"),
        "degree": surface_identity.get("degree", "unknown"),
        "instance": surface_identity.get("instance", "unknown"),
        "collection": surface_identity.get("collection", "unknown"),
        "provider": entry.get("source_id"),
        "core_scope": "conditional",
        "current_state": current_state,
        "lifecycle": entry.get("lifecycle"),
        "implementation_status": entry.get("implementation_status"),
        "live_status": entry.get("live_status"),
        "federation_status": (
            "enabled" if (entry.get("interfaces") or {}).get("unified_search") else "not_enabled"
        ),
        "contract_status": (
            "live_validated" if entry.get("live_status") == "valid" else "candidate"
        ),
        "official_entry_point": identity.get("source_url"),
        "last_live_check": (entry.get("live_validation") or {}).get("date"),
        "evidence_ids": list(entry.get("evidence_ids") or []),
        "document_capability": entry.get("document_contract") or {},
        "legal_status": entry.get("legal_status", "pending_human_review"),
        "display_name": entry.get("display_name"),
        "category": entry.get("category"),
        "coverage_role": entry.get("coverage_role"),
        "maturity_score": entry.get("maturity_score"),
        "maturity_tier": entry.get("maturity_tier"),
        "quality_tier": quality_entry.get("quality_tier"),
        "quality_score": quality_entry.get("score"),
        "quality_critical_gaps": list(quality_entry.get("critical_gaps") or []),
        "interfaces": entry.get("interfaces") or {},
        "fixture_references": (entry.get("documentation") or {}).get("fixture_references", 0),
        "known_defects": list(entry.get("known_defects") or []),
        "next_action": entry.get("next_action"),
    }
    row["priority"] = _priority(row)
    row["workstream"] = "catalog_reconciliation"
    row["gate_gaps"] = _gate_gaps(row)
    row["missing_information"] = _provider_missing_information(entry)
    row["gold_gates"] = _gold_gates(row)
    row["blockers"] = [gate for gate, passed in row["gold_gates"].items() if not passed]
    row["information_score"] = round(
        1 - (len(row["missing_information"]) / len(PROVIDER_REQUIRED_FIELDS)), 3
    )
    return row


def _surface_track(row: dict[str, Any] | None) -> dict[str, Any]:
    """Return a compact, audit-friendly state for one CJPG/CJSG track."""

    if row is None:
        return {
            "provider": None,
            "state": "not_mapped",
            "live_status": "not_observed",
            "contract_status": "candidate",
            "federation_status": "not_enabled",
            "gold_ready": False,
            "blockers": ["runtime", "degree_contract", "live_status", "federation"],
            "next_action": "official_discovery",
        }
    return {
        "provider": row.get("provider"),
        "state": row.get("current_state"),
        "live_status": row.get("live_status"),
        "contract_status": row.get("contract_status"),
        "federation_status": row.get("federation_status"),
        "gold_ready": all(row.get("gold_gates", {}).values()),
        "blockers": list(row.get("blockers") or []),
        "next_action": row.get("next_action") or row.get("workstream"),
        "last_live_check": row.get("last_live_check"),
        "evidence_ids": list(row.get("evidence_ids") or []),
    }


def _state_authority_rollup(surfaces: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the authoritative 27-TJ CJPG/CJSG inventory.

    A row is absent when the matrix has no surface for that track.  Absence is
    kept distinct from a blocked or empty source so downstream reports cannot
    inflate national coverage.
    """

    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in surfaces:
        authority = str(row.get("authority") or "")
        collection = str(row.get("collection") or "")
        if authority in STATE_AUTHORITIES and collection in {"CJPG", "CJSG"}:
            by_key.setdefault((authority, collection), row)

    rollup: dict[str, Any] = {}
    for authority in STATE_AUTHORITIES:
        cjpg = _surface_track(by_key.get((authority, "CJPG")))
        cjsg = _surface_track(by_key.get((authority, "CJSG")))
        rollup[authority] = {
            "cjpg": cjpg,
            "cjsg": cjsg,
            "gold_ready_tracks": sum(int(track["gold_ready"]) for track in (cjpg, cjsg)),
            "missing_tracks": [
                collection
                for collection, track in (("CJPG", cjpg), ("CJSG", cjsg))
                if not track["gold_ready"]
            ],
            "next_actions": sorted(
                {str(track["next_action"]) for track in (cjpg, cjsg) if not track["gold_ready"]}
            ),
        }
    return rollup


def _discovery_queue(surfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build an executable queue for every surface that is not GOLD yet."""

    state_rank = {
        "contract_pending": 0,
        "discovery_pending": 1,
        "blocked_or_unavailable": 2,
        "live_not_federated": 3,
    }
    scope_rank = {"core": 0, "conditional": 1}
    queue: list[dict[str, Any]] = []
    for row in surfaces:
        state = str(row.get("current_state") or "")
        if state not in state_rank or all(row.get("gold_gates", {}).values()):
            continue
        scope = str(row.get("core_scope") or "conditional")
        if not row.get("provider") and scope == "core":
            batch = "providerless_core"
        elif state == "contract_pending":
            batch = "contract_hardening"
        elif state == "blocked_or_unavailable":
            batch = "blocked_official_alternative"
        elif state == "live_not_federated":
            batch = "promotion_gate"
        else:
            batch = "providerless_conditional" if not row.get("provider") else "adapter_discovery"
        queue.append(
            {
                "surface_id": row.get("surface_id"),
                "authority": row.get("authority"),
                "branch": row.get("branch"),
                "degree": row.get("degree"),
                "instance": row.get("instance"),
                "collection": row.get("collection"),
                "family": row.get("family"),
                "core_scope": scope,
                "batch": batch,
                "priority": row.get("priority"),
                "current_state": state,
                "provider": row.get("provider"),
                "official_entry_point": row.get("official_entry_point"),
                "official_directory": row.get("official_directory"),
                "source_class": row.get("source_class"),
                "missing_information": list(row.get("missing_information") or []),
                "gate_gaps": list(row.get("gate_gaps") or []),
                "next_action": row.get("next_action"),
            }
        )
    queue.sort(
        key=lambda item: (
            scope_rank.get(str(item["core_scope"]), 9),
            state_rank.get(str(item["current_state"]), 9),
            str(item.get("priority") or "P9"),
            str(item.get("branch") or ""),
            str(item.get("authority") or ""),
            str(item.get("collection") or ""),
        )
    )
    return queue


def build() -> dict[str, Any]:
    matrix = _read(MATRIX)
    registry = _read(REGISTRY)
    catalog = _read(CATALOG)
    quality = _read(QUALITY)
    registry_by_surface = {
        str(item.get("surface_id")): item
        for item in registry.get("surfaces", [])
        if item.get("surface_id")
    }
    catalog_by_provider = {
        str(item.get("source_id")): item
        for item in catalog.get("entries", [])
        if item.get("source_id")
    }
    quality_by_provider = {
        str(item.get("source_id")): item
        for item in quality.get("entries", [])
        if item.get("source_id")
    }

    surfaces: list[dict[str, Any]] = []
    matrix_providers: set[str] = set()
    for source in matrix.get("rows", []):
        row = dict(source)
        surface = registry_by_surface.get(str(row.get("surface_id")), {})
        provider = row.get("provider") or surface.get("provider")
        catalog_entry = catalog_by_provider.get(str(provider), {})
        quality_entry = quality_by_provider.get(str(provider), {})
        evidence = list(dict.fromkeys(row.get("evidence_ids") or surface.get("evidence_ids") or []))
        row["provider"] = provider
        row["evidence_ids"] = evidence
        row["priority"] = _priority(row)
        row["workstream"] = _workstream(row)
        row["gate_gaps"] = _gate_gaps(row)
        row["missing_information"] = _missing_information(row)
        row["fixture_references"] = (catalog_entry.get("documentation") or {}).get(
            "fixture_references", 0
        )
        row["catalog_live_evidence"] = catalog_entry.get("live_evidence")
        row["catalog_maturity_score"] = catalog_entry.get("maturity_score")
        row["quality_tier"] = quality_entry.get("quality_tier")
        row["quality_score"] = quality_entry.get("score")
        row["quality_critical_gaps"] = list(quality_entry.get("critical_gaps") or [])
        # Quality metadata must be attached before evaluating the GOLD gate.
        # Computing gates earlier made every non-``maturity=gold`` provider
        # appear to fail quality even when the quality ledger had a gold tier
        # with no critical gaps.
        row["gold_gates"] = _gold_gates(row)
        row["blockers"] = [gate for gate, passed in row["gold_gates"].items() if not passed]
        row["information_score"] = round(
            1 - (len(row["missing_information"]) / len(REQUIRED_FIELDS)), 3
        )
        row["registry_surface_id"] = surface.get("surface_id")
        surfaces.append(row)
        if provider:
            matrix_providers.add(str(provider))

    provider_orphans = [
        _catalog_orphan(entry, quality_by_provider.get(provider))
        for provider, entry in sorted(catalog_by_provider.items())
        if provider not in matrix_providers
    ]

    state_authorities = _state_authority_rollup(surfaces)
    discovery_queue = _discovery_queue(surfaces)

    by_priority = Counter(str(item["priority"]) for item in surfaces)
    by_workstream = Counter(str(item["workstream"]) for item in surfaces)
    by_family: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in surfaces:
        by_family[str(item.get("family"))][str(item.get("current_state"))] += 1

    authorities_by_workstream: dict[str, list[str]] = defaultdict(list)
    for item in surfaces:
        if item["workstream"] != "continuous_monitoring":
            authority = str(item.get("authority"))
            if authority not in authorities_by_workstream[item["workstream"]]:
                authorities_by_workstream[item["workstream"]].append(authority)

    return {
        "schema_version": "national-coverage-gap-map-v2",
        "generated_at": "2026-09-08",
        "source_artifacts": [
            str(MATRIX.relative_to(ROOT)),
            str(REGISTRY.relative_to(ROOT)),
            str(CATALOG.relative_to(ROOT)),
            str(QUALITY.relative_to(ROOT)),
        ],
        "scope": {
            "description": "Todas as superfícies nacionais catalogadas, incluindo superfícies condicionais e agregadas.",
            "promotion_rule": "Nenhuma linha vira cobertura por adapter isolado; exige contrato, fixture, live, qualidade e federação.",
            "empty_result_rule": "bloqueio, timeout, CAPTCHA, WAF, TLS, 403, 429 e schema inválido permanecem estados explícitos.",
        },
        "summary": {
            "surfaces": len(surfaces),
            "catalog_providers": len(catalog_by_provider),
            "catalog_orphans": len(provider_orphans),
            "core_surfaces": sum(1 for item in surfaces if item.get("core_scope") == "core"),
            "conditional_surfaces": sum(
                1 for item in surfaces if item.get("core_scope") == "conditional"
            ),
            "by_priority": dict(sorted(by_priority.items())),
            "by_workstream": dict(sorted(by_workstream.items())),
            "by_current_state": dict(Counter(str(item.get("current_state")) for item in surfaces)),
            "by_family": {
                family: dict(sorted(states.items())) for family, states in sorted(by_family.items())
            },
            "core_unready": sum(
                1
                for item in surfaces
                if item.get("core_scope") == "core"
                and item.get("current_state") != "federated_live"
            ),
            "core_ready_state": sum(
                1
                for item in surfaces
                if item.get("core_scope") == "core"
                and item.get("current_state") == "federated_live"
            ),
            "gold_gate_complete": sum(1 for item in surfaces if all(item["gold_gates"].values())),
            "catalog_orphan_gold_gate_complete": sum(
                1 for item in provider_orphans if all(item["gold_gates"].values())
            ),
            "state_authorities": len(STATE_AUTHORITIES),
            "state_cjpg_gold_ready": sum(
                1 for item in state_authorities.values() if item["cjpg"]["gold_ready"]
            ),
            "state_cjsg_gold_ready": sum(
                1 for item in state_authorities.values() if item["cjsg"]["gold_ready"]
            ),
            "state_authorities_with_both_gold_tracks": sum(
                1 for item in state_authorities.values() if item["gold_ready_tracks"] == 2
            ),
            "discovery_queue": len(discovery_queue),
            "providerless_core": sum(
                1 for item in discovery_queue if item["batch"] == "providerless_core"
            ),
            "providerless_conditional": sum(
                1 for item in discovery_queue if item["batch"] == "providerless_conditional"
            ),
        },
        "priority_authorities": {
            key: sorted(value) for key, value in sorted(authorities_by_workstream.items())
        },
        "state_authorities": state_authorities,
        "surfaces": surfaces,
        "discovery_queue": discovery_queue,
        "provider_orphans": provider_orphans,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Mapa nacional de lacunas de cobertura",
        "",
        "Gerado em `2026-09-08` a partir da matriz nacional, do registro de superfícies e do catálogo de providers.",
        "",
        "## Leitura correta",
        "",
        "Este documento mapeia disponibilidade e evidência; não declara que uma fonte possui acervo integral. Bloqueios permanecem bloqueios e não são convertidos em resultados vazios.",
        "",
        "## Resumo",
        "",
        f"- Superfícies: **{summary['surfaces']}** ({summary['core_surfaces']} core, {summary['conditional_surfaces']} condicionais).",
        f"- Core pronto no estado `federated_live`: **{summary['core_ready_state']}**.",
        f"- Core ainda não pronto: **{summary['core_unready']}**.",
        f"- Providers do catálogo sem binding na matriz: **{summary['catalog_orphans']}** de **{summary['catalog_providers']}**.",
        f"- Superfícies com todos os gates GOLD explícitos: **{summary['gold_gate_complete']}**.",
        f"- Matriz estadual CJPG/CJSG: **{summary['state_cjpg_gold_ready']}/27** CJPG e **{summary['state_cjsg_gold_ready']}/27** CJSG em estado GOLD; **{summary['state_authorities_with_both_gold_tracks']}/27** tribunais com as duas trilhas.",
        "",
        "| Prioridade | Quantidade |",
        "|---|---:|",
    ]
    for priority, count in sorted(summary["by_priority"].items()):
        lines.append(f"| {priority} | {count} |")
    lines.extend(["", "| Frente | Quantidade |", "|---|---:|"])
    for workstream, count in sorted(summary["by_workstream"].items()):
        lines.append(f"| {workstream} | {count} |")
    lines.extend(["", "## Autoridades prioritárias", ""])
    for workstream, authorities in report["priority_authorities"].items():
        lines.append(f"- `{workstream}`: {', '.join(authorities)}")
    lines.extend(
        [
            "",
            "## Fila executavel de descoberta e fechamento",
            "",
            "A fila e derivada da matriz nacional. Execute em lotes de uma a tres superficies; bloqueios permanecem explicitos e nao viram resultados vazios.",
            "",
            "| Lote | Autoridade | Ramo | Grau | Colecao | Provider | Estado | Lacunas | Proxima acao |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for item in report["discovery_queue"]:
        gaps = ", ".join(item["gate_gaps"]) or "-"
        provider = item["provider"] or "-"
        lines.append(
            f"| `{item['batch']}` | `{item['authority']}` | `{item['branch']}` | `{item['degree']}` | `{item['collection']}` | `{provider}` | `{item['current_state']}` | {gaps} | {item.get('next_action') or 'discover_official_entry'} |"
        )
    lines.extend(
        [
            "",
            "## Inventário dos 27 tribunais estaduais",
            "",
            "`GOLD` exige todos os gates técnicos; `federated_live` indica fonte ativa, mas não substitui a auditoria de qualidade. `not_mapped` significa que ainda não há contrato de superfície, e não significa resultado vazio.",
            "",
            "| Tribunal | CJPG | Provider CJPG | CJSG | Provider CJSG | Próxima ação |",
            "|---|---|---|---|---|---|",
        ]
    )
    for authority, item in report["state_authorities"].items():
        cjpg = item["cjpg"]
        cjsg = item["cjsg"]
        cjpg_state = "GOLD" if cjpg["gold_ready"] else str(cjpg["state"])
        cjsg_state = "GOLD" if cjsg["gold_ready"] else str(cjsg["state"])
        actions = ", ".join(item["next_actions"]) or "monitoramento"
        lines.append(
            f"| `{authority}` | `{cjpg_state}` | `{cjpg['provider'] or '—'}` | `{cjsg_state}` | `{cjsg['provider'] or '—'}` | {actions} |"
        )
    lines.extend(
        [
            "",
            "## Critério de promoção",
            "",
            "Uma superfície só pode ser promovida quando possuir:",
            "",
            "- fonte oficial identificada;",
            "- contrato específico de grau/coleção;",
            "- adapter e fixture;",
            "- chamada live bounded válida;",
            "- qualidade canônica e inteiro teor conforme declarado;",
            "- integração federada explícita.",
            "",
        ]
    )
    lines.append(
        "A lista completa, com campos faltantes e gates por superfície, está no JSON desta mesma pasta."
    )
    if report.get("provider_orphans"):
        lines.extend(
            [
                "",
                "## Providers do catalogo sem binding na matriz",
                "",
                "Estas entradas continuam visiveis para reconciliacao, mas nao alteram as contagens de cobertura obrigatoria.",
                "",
                "| Provider | Estado | Frente | Informacao faltante |",
                "|---|---|---|---|",
            ]
        )
        for item in report["provider_orphans"]:
            missing = ", ".join(item["missing_information"]) or "-"
            lines.append(
                f"| `{item['provider']}` | `{item['current_state']}` | `{item['workstream']}` | {missing} |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write JSON and Markdown outputs")
    args = parser.parse_args()
    report = build()
    if args.write:
        OUT_JSON.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        OUT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
