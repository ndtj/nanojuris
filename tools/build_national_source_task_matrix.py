"""Build the national source inventory and executable discovery task matrix.

The matrix is deliberately conservative: an authority is enumerated even when
NanoJuris has no adapter yet, but an official endpoint is never guessed.  Rows
without a catalogued source receive ``discover_official_entry`` as their next
action and remain outside the federated rollout.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/coverage/surface-state-registry-20260902.json"
CATALOG = ROOT / "docs/registry/provider-catalog.full.json"
JUSCRAPER = ROOT / "docs/provider-discovery/juscraper-court-inventory-20260906.json"
OUT_JSON = (
    ROOT
    / "specs/changes/0098-national-jurisprudence-gold-coverage/"
    / "national-source-task-matrix.json"
)
OUT_MD = (
    ROOT
    / "specs/changes/0098-national-jurisprudence-gold-coverage/"
    / "national-source-task-matrix.md"
)


STATE_AUTHORITIES = [
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
]
TRF_AUTHORITIES = [f"TRF{i}" for i in range(1, 7)]
TRT_AUTHORITIES = [f"TRT{i}" for i in range(1, 25)]
TRE_AUTHORITIES = [
    "TREAC",
    "TREAL",
    "TREAP",
    "TREAM",
    "TREBA",
    "TRECE",
    "TREDF",
    "TREES",
    "TREGO",
    "TREMA",
    "TREMT",
    "TREMS",
    "TREMG",
    "TREPA",
    "TREPB",
    "TREPR",
    "TREPE",
    "TREPI",
    "TRERJ",
    "TRERN",
    "TRERS",
    "TRERO",
    "TRERR",
    "TRESC",
    "TRESP",
    "TRESE",
    "TRETO",
]
MILITARY_AUTHORITIES = ["TJMSP", "TJMMG", "TJMRS", "STM"]
TCE_AUTHORITIES = [
    "TCEAC",
    "TCEAL",
    "TCEAP",
    "TCEAM",
    "TCEBA",
    "TCECE",
    "TCDF",
    "TCEES",
    "TCEGO",
    "TCEMA",
    "TCEMT",
    "TCEMS",
    "TCEMG",
    "TCEPA",
    "TCEPB",
    "TCEPR",
    "TCEPE",
    "TCEPI",
    "TCERJ",
    "TCERN",
    "TCERO",
    "TCERR",
    "TCERS",
    "TCESC",
    "TCESE",
    "TCESP",
    "TCETO",
]
TCM_AUTHORITIES = ["TCMBA", "TCMGO", "TCMPA", "TCMSP"]

CNJ_DIRECTORIES = {
    "state": "https://www.cnj.jus.br/tribunais-de-justica-estaduais/",
    "labor": "https://www.cnj.jus.br/justica-do-trabalho/",
    "military": "https://www.cnj.jus.br/tribunais-de-justica-militar/",
    "electoral": "https://www.cnj.jus.br/justica-eleitoral-/",
    "all": "https://www.cnj.jus.br/relatorio-por-tribunal/",
}

# Institutional generic rows can be backed by a validated technical surface.
# Keep that binding explicit so the matrix does not create a false discovery
# gap or count a second provider.
SURFACE_ALIASES: dict[tuple[str, str, str, str], tuple[str, str, str, str]] = {
    ("TRF2", "federal", "second", "JURISPRUDENCIA"): (
        "TRF2",
        "federal",
        "second",
        "EPROC",
    ),
    ("TRF4", "federal", "second", "JURISPRUDENCIA"): (
        "TRF4",
        "federal",
        "second",
        "EPROC",
    ),
    ("TRF6", "federal", "second", "JURISPRUDENCIA"): (
        "TRF6",
        "federal",
        "second",
        "EPROC",
    ),
    # TNU exposes its public textual jurisprudence through the validated
    # EPROC module. Keep the generic PORTAL row visible but avoid a duplicate
    # provider or an artificial discovery gap.
    ("TNU", "federal", "superior", "PORTAL"): (
        "TNU",
        "federal",
        "superior",
        "EPROC",
    ),
}

# A provider can be implemented and live-validated before it is promoted to
# the default federation. Bind that evidence to the canonical TRT8 appellate
# surface once the promotion gates are closed.
SURFACE_PROVIDER_OVERRIDES: dict[tuple[str, str, str, str], dict[str, Any]] = {
    ("TRT8", "labor", "second", "JURISPRUDENCIA"): {
        "provider": "trt8_pje_jurisprudencia",
        "official_entry_point": "https://pje.trt8.jus.br/jurisprudencia/",
        "live_status": "valid",
        "last_live_check": "2026-09-09",
        "contract_status": "live_validated",
        "federation_status": "enabled",
        "current_state": "federated_live",
        "evidence_ids": [
            "docs/provider-discovery/trt8-pje-jurisprudencia-live-20260909.json",
            "docs/provider-discovery/trt8-pje-federated-smoke-20260909.json",
            "docs/provider-discovery/trt8-pje-federated-smoke-recheck-20260909.json",
            "docs/provider-discovery/trt8-pje-federated-smoke-20260909-timeout30.json",
        ],
        "next_action": "monitor_live_quality_and_schema_drift",
    },
    # TRT6 exposes both an official PJe SPA and a legacy acórdãos form.  The
    # public search boundary is a reCAPTCHA, so keep the binding diagnostic
    # and opt-in rather than leaving the official surface unrecorded.
    ("TRT6", "labor", "second", "JURISPRUDENCIA"): {
        "provider": "trt6_jurisprudencia",
        "official_entry_point": "https://pje.trt6.jus.br/jurisprudencia/",
        "current_state": "blocked_or_unavailable",
        "live_status": "access_control_required",
        "last_live_check": "2026-09-10",
        "contract_status": "pending",
        "federation_status": "not_enabled",
        "evidence_ids": [
            "docs/provider-discovery/trt6-jurisprudencia-live-20260910.json",
            "docs/providers/trt6_jurisprudencia/README.md",
        ],
        "next_action": "obtain_authorized_non_captcha_search_contract",
    },
    # The military courts have distinct public surfaces and must not be
    # collapsed into the generic PORTAL discovery rows.  These bindings are
    # deliberately conservative: TJMMG and TJMSP remain diagnostic/contextual
    # until a bounded general-search contract is proven; TJMRS is live but its
    # exact-process route is not yet a general federated search.
    ("TJMMG", "military", "second", "PORTAL"): {
        "provider": "tjmmg_jurisprudencia_api",
        "official_entry_point": "https://jurisprudencia.tjmmg.jus.br",
        "current_state": "contract_pending",
        "live_status": "contract_pending_response_limit",
        "last_live_check": "2026-09-09",
        "contract_status": "pending",
        "federation_status": "not_enabled",
        "evidence_ids": [
            "docs/provider-discovery/tjm-mg-jurisprudencia-api-live-20260909.json",
            "docs/providers/tjmmg_jurisprudencia_api/README.md",
        ],
        "next_action": "obtain_bounded_search_contract",
    },
    ("TJMRS", "military", "second", "PORTAL"): {
        "provider": "tjmrs_jurisprudencia",
        "official_entry_point": "https://www.tjmrs.jus.br/abreJurisprudencia.php",
        "current_state": "live_not_federated",
        "live_status": "valid",
        "last_live_check": "2026-09-09",
        "contract_status": "partial",
        "federation_status": "not_enabled",
        "evidence_ids": [
            "docs/provider-discovery/tjmrs-jurisprudencia-live-20260909.json",
            "docs/providers/tjmrs_jurisprudencia/README.md",
        ],
        "document_capability": {
            "status": "declared",
            "supports_full_text": True,
            "full_text_access": "direct",
            "formats": ["html"],
            "document_types": ["acordao"],
        },
        "next_action": "obtain_general_search_contract",
    },
    ("TJMSP", "military", "second", "PORTAL"): {
        "provider": "tjmsp_jurisprudencia",
        "official_entry_point": "https://jurisprudencia-client.tjmsp.jus.br",
        "current_state": "blocked_or_unavailable",
        "live_status": "access_control_required",
        "last_live_check": "2026-09-10",
        "contract_status": "pending",
        "federation_status": "not_enabled",
        "evidence_ids": [
            "docs/provider-discovery/tjmsp-jurisprudencia-live-recheck-20260910.json",
            "docs/providers/tjmsp_jurisprudencia/README.md",
        ],
        "next_action": "obtain_official_allowlist_or_alternative",
    },
}

# Official textual surfaces whose existence is proven, but whose public query
# host currently rejects a bounded unauthenticated request. Keep them in the
# national matrix as explicit external blockers instead of leaving them in the
# discovery queue or treating the response as an empty result.
BLOCKED_SURFACES: dict[tuple[str, str, str, str], dict[str, Any]] = {
    (
        "TRT3",
        "labor",
        "second",
        "JURISPRUDENCIA",
    ): {
        "official_entry_point": "https://juris.trt3.jus.br/juris/consultaBaseCompleta.htm",
        "last_live_check": "2026-09-09",
        "evidence_ids": ["docs/provider-discovery/trt3-jurisprudencia-route-live-20260909.json"],
        "reason": (
            "Official portal links the textual second-degree search, but CloudFront "
            "returns HTTP 403."
        ),
    },
    (
        "TRT4",
        "labor",
        "second",
        "JURISPRUDENCIA",
    ): {
        "official_entry_point": "https://pesquisatextual.trt4.jus.br/",
        "last_live_check": "2026-09-09",
        "evidence_ids": ["docs/provider-discovery/trt4-jurisprudencia-route-live-20260909.json"],
        "reason": (
            "Official portal documents textual second-degree search, but CloudFront "
            "returns HTTP 403."
        ),
    },
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _catalog_index(catalog: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in _as_list(catalog.get("entries")):
        source_id = entry.get("source_id")
        if source_id:
            index[str(source_id)].append(entry)
    return index


def _registry_indexes(
    registry: dict[str, Any],
) -> tuple[dict[tuple[str, str, str, str], list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    surfaces: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    by_id: dict[str, dict[str, Any]] = {}
    for surface in _as_list(registry.get("surfaces")):
        by_id[str(surface.get("surface_id"))] = surface
        key = (
            str(surface.get("authority", "")),
            str(surface.get("branch", "")),
            str(surface.get("degree", "")),
            str(surface.get("collection", "")),
        )
        surfaces[key].append(surface)
    return surfaces, by_id


def _juscraper_authority(source_id: str) -> str:
    normalized = source_id.lower()
    if normalized == "tjdft":
        return "TJDFT"
    if normalized.startswith("tj") or normalized.startswith("trf"):
        return normalized.upper()
    return normalized.upper()


def _source_url(provider: str | None, catalog_index: dict[str, list[dict[str, Any]]]) -> str | None:
    if not provider:
        return None
    if provider.startswith("tre_") and provider.endswith("_sjur_jurisprudencia"):
        # Per-UF candidates share the official electoral jurisprudence SPA.
        # The route itself is recorded in the bounded evidence artifact; this
        # field remains the human-facing official entry point.
        return "https://jurisprudencia-tres.tse.jus.br/"
    for entry in catalog_index.get(provider, []):
        identity = entry.get("identity") or {}
        url = identity.get("source_url")
        if url:
            return str(url)
    return None


def _catalog_entry(
    provider: str | None, catalog_index: dict[str, list[dict[str, Any]]]
) -> dict[str, Any] | None:
    if not provider:
        return None
    entries = catalog_index.get(provider, [])
    return entries[0] if entries else None


def _state_for(
    matches: list[dict[str, Any]],
    catalog_index: dict[str, list[dict[str, Any]]],
) -> tuple[str, dict[str, Any] | None, str | None]:
    if not matches:
        return "discovery_pending", None, None
    # Prefer a row with a provider and then the most complete live state.
    ordered = sorted(
        matches,
        key=lambda row: (
            bool(row.get("provider")),
            row.get("live_status") == "valid",
            row.get("contract_status") == "valid",
            row.get("federation_status") == "enabled",
        ),
        reverse=True,
    )
    row = ordered[0]
    provider = row.get("provider")
    if not provider:
        state = "discovery_pending"
    elif row.get("federation_status") == "enabled" and row.get("live_status") == "valid":
        state = "federated_live"
    elif row.get("live_status") in {
        "access_controlled",
        "access_control_required",
        "blocked_transport",
        "source_unavailable",
    }:
        state = "blocked_or_unavailable"
    elif row.get("contract_status") in {"candidate", "pending_contract"}:
        state = "contract_pending"
    elif row.get("live_status") == "valid":
        state = "live_not_federated"
    else:
        state = "implementation_pending"
    return state, row, _source_url(str(provider), catalog_index)


def _next_action(state: str, *, core: bool) -> str:
    if state == "discovery_pending":
        return "discover_official_entry"
    if state == "blocked_or_unavailable":
        return "recheck_official_alternative_or_record_block"
    if state == "contract_pending":
        return "close_contract_filters_pagination_and_fixtures"
    if state == "live_not_federated":
        return "complete_quality_and_promotion_gates"
    if state == "implementation_pending":
        return "implement_independent_adapter_and_bounded_live_check"
    if state == "federated_live":
        return "monitor_live_quality_and_schema_drift"
    return "discover_official_entry" if core else "scope_decision"


def _task_for(family: str, state: str) -> list[str]:
    family_task = {
        "state_cjpg": "T047",
        "state_cjsg": "T048",
        "state_alternates": "T049",
        "federal": "T050",
        "superior": "T051",
        "labor": "T052",
        "electoral": "T053",
        "military": "T054",
        "conditional": "T055",
    }[family]
    tasks = [family_task]
    if state == "discovery_pending":
        tasks.append("T056")
    elif state in {"implementation_pending", "contract_pending"}:
        tasks.extend(["T057", "T058"])
    elif state in {"live_not_federated", "blocked_or_unavailable"}:
        tasks.extend(["T059", "T060"])
    return tasks


def _surface_id(authority: str, collection: str, degree: str, provider: str | None) -> str:
    suffix = provider or "gap"
    return f"inventory:{authority.lower()}:{collection.lower()}:{degree}:{suffix}"


def _make_row(
    *,
    authority: str,
    branch: str,
    degree: str,
    instance: str,
    collection: str,
    family: str,
    core_scope: str,
    matches: list[dict[str, Any]],
    catalog_index: dict[str, list[dict[str, Any]]],
    source_class: str,
    official_directory: str,
) -> dict[str, Any]:
    state, current, source_url = _state_for(matches, catalog_index)
    provider = current.get("provider") if current else None
    catalog_entry = _catalog_entry(str(provider) if provider else None, catalog_index)
    evidence = _as_list(current.get("evidence_ids")) if current else []
    document_capability = current.get("document_capability") if current else None
    if document_capability is None and catalog_entry:
        document_capability = catalog_entry.get("document_contract")
    return {
        "task_id": _task_for(family, state),
        "authority": authority,
        "branch": branch,
        "degree": degree,
        "instance": instance,
        "collection": collection,
        "family": family,
        "core_scope": core_scope,
        "source_class": source_class,
        "surface_id": _surface_id(authority, collection, degree, provider),
        "provider": provider,
        "official_entry_point": source_url,
        "official_directory": official_directory,
        "coverage_role": catalog_entry.get("coverage_role") if catalog_entry else None,
        "category": catalog_entry.get("category") if catalog_entry else None,
        "current_state": state,
        "lifecycle": current.get("lifecycle") if current else "candidate",
        "maturity": current.get("maturity") if current else "unknown",
        "live_status": current.get("live_status") if current else "not_observed",
        "last_live_check": current.get("last_live_check") if current else None,
        "contract_status": current.get("contract_status") if current else "candidate",
        "federation_status": current.get("federation_status") if current else "not_enabled",
        "legal_status": current.get("legal_status") if current else "pending_human_review",
        "document_capability": document_capability,
        "evidence_ids": evidence,
        "next_action": _next_action(state, core=core_scope == "core"),
        "promotion_rule": "eight_gate_contract_live_fixture_quality_federation"
        if core_scope == "core"
        else "separate_scope_decision_before_promotion",
    }


def build() -> dict[str, Any]:
    registry = _load(REGISTRY)
    catalog = _load(CATALOG)
    juscraper = _load(JUSCRAPER)
    catalog_index = _catalog_index(catalog)
    registry_index, registry_by_id = _registry_indexes(registry)
    rows: list[dict[str, Any]] = []

    def add_core(authorities: list[str], branch: str, family: str, collection: str) -> None:
        for authority in authorities:
            degree = "first" if family == "state_cjpg" else "second"
            key = (authority, branch, degree, collection)
            matches = registry_index.get(key, [])
            row = _make_row(
                authority=authority,
                branch=branch,
                degree=degree,
                instance=degree,
                collection=collection,
                family=family,
                core_scope="core",
                matches=matches,
                catalog_index=catalog_index,
                source_class="official_court_jurisprudence",
                official_directory=CNJ_DIRECTORIES.get(branch, CNJ_DIRECTORIES["all"]),
            )
            blocked = BLOCKED_SURFACES.get(key)
            if blocked and not matches:
                row.update(
                    {
                        "official_entry_point": blocked["official_entry_point"],
                        "current_state": "blocked_or_unavailable",
                        "live_status": "access_blocked",
                        "last_live_check": blocked["last_live_check"],
                        "contract_status": "candidate",
                        "next_action": "recheck_official_alternative_or_record_block",
                        "evidence_ids": list(blocked["evidence_ids"]),
                        "blocking_reason": blocked["reason"],
                    }
                )
            rows.append(row)

    add_core(STATE_AUTHORITIES, "state", "state_cjpg", "CJPG")
    add_core(STATE_AUTHORITIES, "state", "state_cjsg", "CJSG")

    # Every currently registered surface is retained, including alternate,
    # contextual and blocked sources not represented by the canonical pairs.
    seen = {(row["authority"], row["collection"], row["degree"], row["provider"]) for row in rows}
    for surface in registry_by_id.values():
        identity = (
            surface.get("authority"),
            surface.get("collection"),
            surface.get("degree"),
            surface.get("provider"),
        )
        if identity in seen:
            continue
        branch = str(surface.get("branch") or "unknown")
        rows.append(
            _make_row(
                authority=str(surface.get("authority")),
                branch=branch,
                degree=str(surface.get("degree") or "unknown"),
                instance=str(surface.get("instance") or "unknown"),
                collection=str(surface.get("collection") or "UNKNOWN"),
                family="state_alternates",
                core_scope="core"
                if branch in {"state", "federal", "labor", "electoral"}
                else "conditional",
                matches=[surface],
                catalog_index=catalog_index,
                source_class="registered_surface",
                official_directory=CNJ_DIRECTORIES.get(branch, CNJ_DIRECTORIES["all"]),
            )
        )
        seen.add(identity)

    # Preserve upstream Juscraper surfaces that do not yet have a NanoJuris
    # equivalent.  CPOPG/CPOSG/detail are intentionally semantic-pending: the
    # name alone is not proof of textual jurisprudence or degree.
    for record in _as_list(juscraper.get("records")):
        source_id = str(record.get("source_id") or "")
        authority = _juscraper_authority(source_id)
        for upstream_surface in _as_list(record.get("surfaces")):
            if upstream_surface in {"cjsg", "cjpg"}:
                continue
            collection = str(upstream_surface).upper()
            provider = (record.get("surface_equivalents") or {}).get(upstream_surface)
            identity = (authority, collection, "unknown", provider)
            if identity in seen:
                continue
            rows.append(
                _make_row(
                    authority=authority,
                    branch="state" if authority.startswith("TJ") else "federal",
                    degree="unknown",
                    instance="unknown",
                    collection=collection,
                    family="state_alternates",
                    core_scope="conditional",
                    matches=[],
                    catalog_index=catalog_index,
                    source_class="juscraper_surface_semantics_pending",
                    official_directory=CNJ_DIRECTORIES.get(
                        "state" if authority.startswith("TJ") else "federal",
                        CNJ_DIRECTORIES["all"],
                    ),
                )
            )
            row = rows[-1]
            row["provider"] = provider
            row["upstream_reference"] = {
                "source_id": source_id,
                "upstream_package": record.get("upstream_package"),
                "upstream_client_class": record.get("upstream_client_class"),
                "surface": upstream_surface,
                "classification": record.get("classification"),
            }
            row["next_action"] = "confirm_upstream_surface_semantics_before_adapter"
            seen.add(identity)

    def add_single(
        authority: str,
        branch: str,
        degree: str,
        collection: str,
        family: str,
        core_scope: str,
        source_class: str = "official_court_jurisprudence",
    ) -> None:
        key = (authority, branch, degree, collection)
        matches = registry_index.get(key, [])
        alias_target = SURFACE_ALIASES.get(key)
        if not matches and alias_target:
            matches = registry_index.get(alias_target, [])
        row = _make_row(
            authority=authority,
            branch=branch,
            degree=degree,
            instance=degree,
            collection=collection,
            family=family,
            core_scope=core_scope,
            matches=matches,
            catalog_index=catalog_index,
            source_class=(
                "official_court_jurisprudence_alias" if alias_target and matches else source_class
            ),
            official_directory=CNJ_DIRECTORIES.get(branch, CNJ_DIRECTORIES["all"]),
        )
        override = SURFACE_PROVIDER_OVERRIDES.get(key)
        if override:
            provider = str(override["provider"])
            catalog_entry = _catalog_entry(provider, catalog_index) or {}
            row.update(override)
            row["provider"] = provider
            row["surface_id"] = _surface_id(authority, collection, degree, provider)
            row["coverage_role"] = catalog_entry.get("coverage_role")
            row["category"] = catalog_entry.get("category")
            row["lifecycle"] = catalog_entry.get("lifecycle", "candidate")
            row["maturity"] = catalog_entry.get("maturity_tier", "mapped")
            row["document_capability"] = catalog_entry.get("document_contract")
            row["promotion_rule"] = "eight_gate_contract_live_fixture_quality_federation"
        if alias_target and matches:
            # Keep the generic institutional row visible, but make the
            # technical binding auditable instead of creating a duplicate
            # provider or an artificial discovery gap.
            row["coverage_alias_of"] = [
                str(match.get("surface_id")) for match in matches if match.get("surface_id")
            ]
            if authority == "TNU":
                row["alias_reason"] = (
                    "TNU exposes its public textual jurisprudence search through "
                    "the validated EPROC module; the TNU origin filter and sample "
                    "records prove the superior-court scope."
                )
            else:
                row["alias_reason"] = (
                    f"{authority} exposes the public second-degree jurisprudence "
                    "search through its EPROC surface; the origin filter proves "
                    "the federal appellate scope."
                )
        blocked = BLOCKED_SURFACES.get(key)
        if blocked and not matches:
            row.update(
                {
                    "official_entry_point": blocked["official_entry_point"],
                    "current_state": "blocked_or_unavailable",
                    "live_status": "access_blocked",
                    "last_live_check": blocked["last_live_check"],
                    "contract_status": "candidate",
                    "next_action": "recheck_official_alternative_or_record_block",
                    "evidence_ids": list(blocked["evidence_ids"]),
                    "blocking_reason": blocked["reason"],
                }
            )
        rows.append(row)

    for authority in TRF_AUTHORITIES:
        add_single(authority, "federal", "second", "JURISPRUDENCIA", "federal", "core")
    add_single("CJF", "federal", "superior", "JURISPRUDENCIA", "federal", "core")
    for authority in ["STF", "STJ", "STM", "TNU", "TST", "TSE", "CNJ", "CSJT"]:
        branch = (
            "constitutional"
            if authority == "STF"
            else "electoral"
            if authority == "TSE"
            else "labor"
            if authority == "TST"
            else "superior"
            if authority == "STJ"
            else "military"
            if authority == "STM"
            else "federal"
        )
        scope = "conditional" if authority in {"CNJ", "CSJT"} else "core"
        add_single(
            authority, branch, "superior", "PORTAL", "superior", scope, "official_superior_court"
        )
    for authority in TRT_AUTHORITIES:
        key = (authority, "labor", "second", "JURISPRUDENCIA")
        add_single(authority, "labor", "second", "JURISPRUDENCIA", "labor", "core")
        # Unlike an unresearched row, these two authorities have an official
        # textual surface already proven by their portals; only the query
        # host is externally blocked. Apply the same explicit blocker state
        # used by the canonical state/federal rows.
        blocked = BLOCKED_SURFACES.get(key)
        if blocked:
            row = rows[-1]
            row.update(
                {
                    "official_entry_point": blocked["official_entry_point"],
                    "current_state": "blocked_or_unavailable",
                    "live_status": "access_blocked",
                    "last_live_check": blocked["last_live_check"],
                    "contract_status": "candidate",
                    "next_action": "recheck_official_alternative_or_record_block",
                    "evidence_ids": list(blocked["evidence_ids"]),
                    "blocking_reason": blocked["reason"],
                }
            )
    for authority in TRE_AUTHORITIES:
        add_single(authority, "electoral", "second", "SJUR", "electoral", "core")
        # The metadata adapter is not the decision-search implementation.  A
        # bounded official SJUR/TRE family now exists for every UF, but its
        # pagination and document gates remain open; bind the rows to that
        # executable family without promoting them to federation.
        row = rows[-1]
        family_entry = _catalog_entry("tre_sjur_jurisprudencia", catalog_index) or {}
        row.update(
            {
                "task_id": _task_for("electoral", "contract_pending"),
                "provider": "tre_sjur_jurisprudencia",
                "surface_id": _surface_id(authority, "SJUR", "second", "tre_sjur_jurisprudencia"),
                "official_entry_point": "https://jurisprudencia-tres.tse.jus.br/",
                "current_state": "contract_pending",
                "live_status": "valid",
                "last_live_check": "2026-09-10",
                "contract_status": "partial",
                "federation_status": "not_enabled",
                "coverage_role": family_entry.get("coverage_role"),
                "category": family_entry.get("category"),
                "lifecycle": family_entry.get("lifecycle", "implemented"),
                "maturity": family_entry.get("maturity_tier", "context"),
                "document_capability": family_entry.get("document_contract"),
                "evidence_ids": [
                    "docs/provider-discovery/tre-sjur-route-inventory-live-20260909.json",
                    "docs/provider-discovery/tre-sjur-gold-live-20260909.json",
                    "docs/provider-discovery/tre-sp-sjur-pagination-live-20260909.json",
                    "docs/provider-discovery/tre-sp-sjur-runtime-live-20260910.json",
                ],
                "next_action": "close_remote_pagination_and_document_gates",
                "blocking_reason": (
                    "A rota textual publica foi validada; paginação remota e inteiro teor "
                    "por UF ainda não foram comprovados."
                ),
            }
        )
    for authority in MILITARY_AUTHORITIES:
        if authority == "STM":
            continue
        add_single(authority, "military", "second", "PORTAL", "military", "core")
    for authority in TCE_AUTHORITIES:
        add_single(
            authority,
            "control",
            "second",
            "JURISPRUDENCIA",
            "conditional",
            "conditional",
            "control_court",
        )
    for authority in TCM_AUTHORITIES:
        add_single(
            authority,
            "control",
            "second",
            "JURISPRUDENCIA",
            "conditional",
            "conditional",
            "control_court",
        )

    # Deduplicate synthetic rows introduced by an existing alternate surface.
    unique: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for row in rows:
        override_key = (
            str(row.get("authority")),
            str(row.get("branch")),
            str(row.get("degree")),
            str(row.get("collection")),
        )
        if not row.get("provider") and override_key in SURFACE_PROVIDER_OVERRIDES:
            # The provider override is the canonical binding for this surface;
            # drop the generic gap row produced by the older registry snapshot.
            continue
        key = (
            row["authority"],
            row["branch"],
            row["degree"],
            row["collection"],
            row["provider"] or "",
        )
        unique[key] = row
    rows = sorted(
        unique.values(),
        key=lambda row: (
            row["branch"],
            row["authority"],
            row["degree"],
            row["collection"],
            row["provider"] or "",
        ),
    )
    counts = Counter(row["current_state"] for row in rows)
    family_counts = Counter(row["family"] for row in rows)
    return {
        "schema_version": "1.0",
        "kind": "national_source_task_matrix",
        "generated_at": date.today().isoformat(),
        "authority": {
            "official_directories": {
                "cnj_state": CNJ_DIRECTORIES["state"],
                "cnj_labor": CNJ_DIRECTORIES["labor"],
                "cnj_electoral": CNJ_DIRECTORIES["electoral"],
                "cnj_military": CNJ_DIRECTORIES["military"],
                "cnj_all": CNJ_DIRECTORIES["all"],
            },
            "source_note": (
                "Directory links are discovery anchors only; each row requires "
                "an official route and bounded live evidence before promotion."
            ),
            "live_directory_evidence": (
                "docs/provider-discovery/national-directory-live-20260908.json"
            ),
            "juscraper_inventory": (
                "docs/provider-discovery/juscraper-court-inventory-20260906.json"
            ),
        },
        "summary": {
            "rows": len(rows),
            "core_rows": sum(row["core_scope"] == "core" for row in rows),
            "conditional_rows": sum(row["core_scope"] == "conditional" for row in rows),
            "by_current_state": dict(sorted(counts.items())),
            "by_family": dict(sorted(family_counts.items())),
            "juscraper_semantics_pending": sum(
                row["source_class"] == "juscraper_surface_semantics_pending" for row in rows
            ),
            "remaining_task_ids": sorted({task for row in rows for task in row["task_id"]}),
        },
        "rows": rows,
    }


def render_markdown(matrix: dict[str, Any]) -> str:
    summary = matrix["summary"]
    lines = [
        "# Matriz nacional de fontes e tarefas — SDD 0098",
        "",
        f"Gerada em `{matrix['generated_at']}` por `tools/build_national_source_task_matrix.py`.",
        (
            "A matriz enumera fontes existentes e superfícies ainda não descobertas; "
            "não afirma que uma rota ou provider funciona."
        ),
        "",
        "## Escopo e regra de promoção",
        "",
        (
            f"- Linhas: **{summary['rows']}** ({summary['core_rows']} core; "
            f"{summary['conditional_rows']} condicionais)."
        ),
        (
            "- Core: jurisprudência textual oficial de TJs, TRFs/CJF, superiores, "
            "TRTs/TST, TSE/TREs e Justiça Militar."
        ),
        (
            "- Condicional: tribunais de contas e outras fontes administrativas; "
            "exigem decisão de escopo antes de contar na cobertura judicial."
        ),
        "- `discovery_pending` nunca é vazio e nunca entra na federação.",
        (
            f"- Superfícies Juscraper sem equivalente/semântica confirmada: "
            f"**{summary['juscraper_semantics_pending']}**; exigem análise "
            "antes de qualquer adapter."
        ),
        (
            "- Promoção exige contrato, fixture, chamada live bounded, qualidade "
            "canônica e federação; bloqueios permanecem explícitos."
        ),
        "",
        "## Diretórios oficiais de descoberta",
        "",
    ]
    for name, url in matrix["authority"]["official_directories"].items():
        lines.append(f"- `{name}`: {url}")
    lines.append(
        "- Evidência live bounded: `docs/provider-discovery/national-directory-live-20260908.json`"
    )
    lines.extend(
        [
            "",
            "## Estado atual",
            "",
            "| Estado | Linhas |",
            "| --- | ---: |",
        ]
    )
    for state, count in sorted(summary["by_current_state"].items()):
        lines.append(f"| `{state}` | {count} |")
    lines.extend(["", "## Lacunas prioritárias", ""])
    priority_groups = [
        ("CJPG não federado", "state_cjpg", None),
        ("CJSG não federado", "state_cjsg", None),
        ("Federal sem descoberta", "federal", "discovery_pending"),
        ("Trabalho sem descoberta", "labor", "discovery_pending"),
        ("Militar sem descoberta", "military", "discovery_pending"),
    ]
    for label, family, state in priority_groups:
        selected = [
            row["authority"]
            for row in matrix["rows"]
            if row["family"] == family
            and (
                row["current_state"] != "federated_live"
                if state is None
                else row["current_state"] == state
            )
        ]
        lines.append(f"- **{label}:** {', '.join(selected) if selected else 'nenhuma'}.")
    lines.extend(
        [
            "",
            "## Tarefas rastreáveis",
            "",
            (
                "A execução deve usar os IDs abaixo em lotes de até três fontes. "
                "Cada linha no JSON contém `task_id`, provider atual, evidências, "
                "ação seguinte e diretório oficial."
            ),
            "",
            "| ID | Família | Escopo | Ação |",
            "| --- | --- | --- | --- |",
            "| T047 | CJPG | 27 TJs | inventariar e fechar primeiro grau |",
            "| T048 | CJSG | 27 TJs | inventariar e fechar segundo grau |",
            (
                "| T049 | Alternativas | fontes registradas | validar ementários, "
                "eproc, PJe, portais e turmas |"
            ),
            "| T050 | Federal | TRF1–TRF6/CJF | descobrir e validar jurisprudência federal |",
            (
                "| T051 | Superiores | STF/STJ/STM/TNU/TST/TSE/CSJT/CNJ | separar "
                "jurisprudência de contexto |"
            ),
            "| T052 | Trabalho | TRT1–TRT24 | descobrir rota oficial e contrato |",
            "| T053 | Eleitoral | TSE/TREs | validar SJUR e fontes locais |",
            "| T054 | Militar | TJMs/STM | validar segundo grau militar |",
            "| T055 | Condicional | TCEs/TCMs | decidir escopo antes da promoção |",
            "| T056 | Descoberta | todas as lacunas | localizar rota oficial/API/exportação |",
            "| T057 | Live | fontes descobertas | chamada bounded, filtros e paginação |",
            (
                "| T058 | Contrato | fontes com resposta | adapter, fixtures, "
                "inteiro teor e qualidade |"
            ),
            "| T059 | Federação | fontes elegíveis | smoke opt-in e promoção técnica |",
            (
                "| T060 | Reconciliação | fontes bloqueadas/divergentes | manter "
                "estado explícito e atualizar ledger |"
            ),
            "",
            "## Limites",
            "",
            (
                "A matriz não autoriza bypass de CAPTCHA, WAF, Turnstile, login, "
                "rate limit ou TLS. Quando o diretório oficial existe mas a "
                "consulta exige desafio ou autorização, a linha permanece "
                "`blocked_or_unavailable` e a evidência deve apontar a ação "
                "externa necessária."
            ),
            "",
            (
                "Fonte institucional para a enumeração dos ramos: [CNJ — Tribunais "
                "de Justiça Estaduais](https://www.cnj.jus.br/tribunais-de-justica-estaduais/), "
                "[CNJ — Justiça do Trabalho](https://www.cnj.jus.br/justica-do-trabalho/), "
                "[CNJ — Justiça Eleitoral](https://www.cnj.jus.br/justica-eleitoral-/) "
                "e [CNJ — Tribunais de Justiça Militar](https://www.cnj.jus.br/tribunais-de-justica-militar/)."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write JSON and Markdown artifacts")
    args = parser.parse_args()
    matrix = build()
    if args.write:
        OUT_JSON.write_text(
            json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        OUT_MD.write_text(render_markdown(matrix), encoding="utf-8")
    else:
        print(json.dumps(matrix["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
