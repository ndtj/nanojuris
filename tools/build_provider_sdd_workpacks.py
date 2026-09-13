"""Build resumable SDD work packs for every NanoJuris provider.

The generator is offline-only. It joins the generated provider catalog with
checked-in dossiers, source contracts, tests, fixtures and versioned discovery
evidence. It never contacts a court and never promotes a provider.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
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

from nanojuris.topology import packaged_topology  # noqa: E402
from tools.audit_provider_discovery_offline import audit as audit_offline  # noqa: E402

CATALOG_PATH = ROOT / "docs" / "registry" / "provider-catalog.full.json"
UNIFIED_PATH = ROOT / "docs" / "provider-discovery" / "unified-contract-matrix.json"
CLOSURE_PATH = ROOT / "docs" / "provider-discovery" / "provider-closure-ledger.json"
OUTPUT_DIR = ROOT / "specs" / "changes" / "0035-provider-completion-autopilot"
WORKPACK_DIR = OUTPUT_DIR / "provider-workpacks"
BASELINE_PATH = OUTPUT_DIR / "provider-baseline.json"
STATE_PATH = OUTPUT_DIR / "execution-state.json"
SUMMARY_PATH = OUTPUT_DIR / "provider-completion-summary.md"

VERSIONED_FIXTURE_KINDS = {"versioned_fixture", "versioned_and_inline"}
TERMINAL_STATES = {
    "accepted",
    "accepted_with_limitations",
    "rejected",
    "deferred_with_review",
    "out_of_scope",
}
LEGACY_STATUS_MIGRATIONS = {
    "complete": "stale",
    "blocked": "waiting_evidence",
    "deferred": "waiting_evidence",
}


def evidence_fingerprint(row: dict[str, Any]) -> str:
    """Return a stable fingerprint for evidence that controls revalidation."""
    payload = {
        "source_id": row.get("source_id"),
        "implementation_status": row.get("implementation_status"),
        "coverage_role": row.get("coverage_role"),
        "maturity_tier": row.get("maturity_tier"),
        "maturity_score": row.get("maturity_score"),
        "target_tier": row.get("target_tier"),
        "priority": row.get("priority"),
        "gaps": row.get("gaps", []),
        "topology_collection_ids": row.get("topology_collection_ids", []),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def _entry_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("source_id", "")): row for row in payload.get("entries", [])}


def _unified_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("source", "")): row for row in payload.get("providers", [])}


def _closure_map(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in payload.get("items", []):
        grouped[str(row.get("source", ""))].append(row)
    return dict(grouped)


def _target_tier(entry: dict[str, Any]) -> str:
    lifecycle = str(entry.get("implementation_status", "unknown"))
    role = str(entry.get("coverage_role", "unknown"))
    if lifecycle == "none":
        return "candidate_contract_confirmed"
    if lifecycle == "family":
        return "family_contract_verified"
    if role == "primary_textual_jurisprudence":
        return "gold"
    return "context_verified"


def _priority(entry: dict[str, Any], gaps: list[str]) -> int:
    lifecycle = str(entry.get("implementation_status", "unknown"))
    role = str(entry.get("coverage_role", "unknown"))
    tier = str(entry.get("maturity_tier", "unknown"))
    live_status = str(entry.get("live_status", ""))
    if lifecycle == "runtime" and role == "primary_textual_jurisprudence":
        if (
            tier in {"blocked", "bronze"}
            or live_status
            in {"blocked", "blocked_access", "blocked_transport", "source_unavailable"}
            or "missing_versioned_fixture" in gaps
        ):
            return 0
        if tier != "gold":
            return 1
        return 2
    if lifecycle == "runtime":
        return 3
    if lifecycle == "none":
        return 4
    return 5


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _gaps(
    entry: dict[str, Any],
    offline: dict[str, Any],
    unified: dict[str, Any],
    closure: list[dict[str, Any]],
) -> list[str]:
    gaps: list[str] = []
    lifecycle = str(entry.get("implementation_status", "unknown"))
    documentation = entry.get("documentation") or {}
    maturity = entry.get("maturity_score") or {}
    live = entry.get("live_validation") or {}
    output = entry.get("output_contract") or {}

    open_items = int(documentation.get("open_items", 0) or 0)
    if open_items:
        gaps.append(f"documentation_open_items:{open_items}")
    if lifecycle == "runtime":
        if not offline.get("runtime_registered", False):
            gaps.append("runtime_registration_not_proven")
        if not offline.get("test_references"):
            gaps.append("missing_provider_test")
        if offline.get("fixture_evidence_kind") not in VERSIONED_FIXTURE_KINDS:
            gaps.append("missing_versioned_fixture")
        if not (entry.get("interfaces") or {}).get("unified_search", False):
            gaps.append("not_in_unified_search")
        live_status = str(live.get("status", "not_recorded"))
        if live_status not in {"valid", "valid_data"}:
            gaps.append(f"live_status:{live_status}")
    elif lifecycle == "none":
        gaps.extend(["candidate_without_runtime", "candidate_without_local_fixture"])

    for blocker in maturity.get("blockers") or []:
        gaps.append(f"maturity:{blocker}")
    for gap in unified.get("gaps") or []:
        gaps.append(f"unified:{gap}")
    if output.get("supports_full_text") and output.get("full_text_access") in {
        None,
        "unknown",
        "not_declared",
    }:
        gaps.append("full_text_contract_unknown")
    if entry.get("known_defects"):
        gaps.append("known_defects_open")
    if any(row.get("status") == "blocked_external" for row in closure):
        gaps.append("external_block_recorded")
    if any(row.get("status") == "candidate_pending_adapter" for row in closure):
        gaps.append("candidate_todos_open")
    return _dedupe(gaps)


def _initial_status(entry: dict[str, Any], gaps: list[str]) -> str:
    lifecycle = str(entry.get("implementation_status", "unknown"))
    if lifecycle == "family":
        return "not_started"
    if lifecycle == "none":
        return "not_started"
    if not gaps and str(entry.get("maturity_tier")) == "gold":
        return "ready_for_review"
    return "not_started"


def _workpack(
    entry: dict[str, Any],
    offline: dict[str, Any],
    unified: dict[str, Any],
    closure: list[dict[str, Any]],
    gaps: list[str],
    state: dict[str, Any] | None = None,
) -> str:
    source = str(entry["source_id"])
    display = str(entry.get("display_name", source))
    documentation = entry.get("documentation") or {}
    input_contract = entry.get("input_contract") or {}
    output_contract = entry.get("output_contract") or {}
    pagination = entry.get("pagination_contract") or {}
    live = entry.get("live_validation") or {}
    maturity = entry.get("maturity_score") or {}
    known_defects = entry.get("known_defects") or []
    completion_state = state or {}
    disposition = completion_state.get("disposition")
    completion_status = completion_state.get("status", "not_started")
    completion_phase = completion_state.get("phase", "inspect")
    review_after = completion_state.get("review_after")
    resume_when = completion_state.get("resume_when")
    next_actions = _dedupe(
        list(maturity.get("next_actions") or [])
        + [str(row.get("next_action", "")) for row in closure]
    )
    tests = offline.get("test_references") or []
    fixtures = offline.get("fixture_references") or []
    filters_text = ", ".join(input_contract.get("supported_filters") or [])
    canonical_text = ", ".join(output_contract.get("canonical_records") or [])
    tasks = (
        [
            "confirmar fonte oficial, rota, método, payload e termos aplicáveis",
            "fechar perguntas do dossier e source contract sem inferência",
            "implementar adapter somente após fixtures e contrato aprovados",
            "criar testes de sucesso, vazio, erro, timeout e schema drift",
            "mapear identidade, campos canônicos, raw e traces",
            "declarar filtros, paginação, ordenação e completude",
            "executar scorecard e decidir promoção ou defer",
        ]
        if entry.get("implementation_status") == "none"
        else [
            "reconciliar capability, dossier, source contract, módulo e interfaces",
            "fechar todos os itens documentais objetivos",
            "garantir fixtures versionadas de sucesso, vazio e falhas críticas",
            "provar identidade, canonicalização, deduplicação, raw e traces",
            "provar filtros, paginação, ordenação, limites e completude",
            "provar estados de acesso, timeout, rate limit e schema drift",
            "provar referência e inteiro teor quando declarados",
            "executar testes locais, tipos, lint e auditorias geradas",
            "executar canário live bounded somente quando autorizado",
            "registrar scorecard, risco residual e decisão de tier",
        ]
    )

    def bullets(values: list[Any], empty: str = "nenhum registrado") -> str:
        return "\n".join(f"- {value}" for value in values) if values else f"- {empty}"

    lines = [
        f"# Work pack — {display}",
        "",
        f"Source ID: {source}",
        f"Lifecycle: {entry.get('implementation_status', 'unknown')}",
        f"Coverage role: {entry.get('coverage_role', 'unknown')}",
        f"Maturity: {entry.get('maturity_tier', 'unknown')}",
        f"Target: {_target_tier(entry)}",
        f"Priority: P{_priority(entry, gaps)}",
        "",
        "## Contrato observado",
        "",
        f"- busca textual: {input_contract.get('text_query', False)}",
        f"- filtros: {filters_text or 'nenhum declarado'}",
        f"- paginação: {input_contract.get('pagination_mode', pagination.get('mode', 'unknown'))}",
        f"- completude: {pagination.get('completeness_contract', 'unknown')}",
        f"- inteiro teor: {output_contract.get('full_text_access', 'unknown')}",
        f"- registros canônicos: {canonical_text or 'nenhum declarado'}",
        f"- busca unificada: {(entry.get('interfaces') or {}).get('unified_search', False)}",
        "",
        "## Evidência local",
        "",
        f"- módulo: {offline.get('module') or 'ausente'}",
        f"- dossier: docs/providers/{source}/README.md",
        f"- source contract: docs/source-contracts/{source}.md",
        f"- readiness documental: {documentation.get('readiness', 'unknown')}",
        f"- itens documentais abertos: {documentation.get('open_items', 0)}",
        f"- fixture evidence: {offline.get('fixture_evidence_kind', 'none')}",
        f"- completion status: {completion_status}",
        f"- completion phase: {completion_phase}",
        f"- disposition: {disposition or 'pending decision'}",
        f"- review after: {review_after or 'not scheduled'}",
        f"- resume when: {resume_when or 'not defined'}",
        "",
        "### Testes",
        "",
        bullets(tests),
        "",
        "### Fixtures",
        "",
        bullets(fixtures),
        "",
        "## Evidência live versionada",
        "",
        f"- status: {live.get('status', 'not_recorded')}",
        f"- data: {live.get('checked_at') or live.get('date') or 'não registrada'}",
        "- esta fotografia não prova disponibilidade atual ou permanente",
        "",
        "## Lacunas consolidadas",
        "",
        bullets(gaps, "nenhuma lacuna automática; revisão humana ainda obrigatória"),
        "",
        "## Defeitos conhecidos",
        "",
        bullets([str(item) for item in known_defects]),
        "",
        "## Tarefas obrigatórias",
        "",
    ]
    if disposition:
        lines.extend(
            [
                "Checklist WP marca que cada item foi avaliado nesta rodada; não",
                "substitui evidência ausente nem converte limitação em sucesso.",
                "",
            ]
        )
        outcome = str(disposition)
        if outcome == "accepted":
            outcome_note = "evidence gate passed; no residual automated gap"
        elif outcome == "accepted_with_limitations":
            outcome_note = "processed; residual limitations remain explicit above"
        else:
            outcome_note = f"processed; resume condition: {resume_when or 'new evidence required'}"
        lines.extend(
            f"- [x] WP-{index:02d} — {task} — outcome: {outcome}; {outcome_note}"
            for index, task in enumerate(tasks, 1)
        )
    else:
        lines.extend(f"- [ ] WP-{index:02d} — {task}" for index, task in enumerate(tasks, 1))
    lines += [
        "",
        "## Próximas ações sugeridas",
        "",
        bullets(next_actions),
        "",
        "## Definition of Done",
        "",
        "- contrato e capability sincronizados;",
        "- fixtures e testes negativos reproduzíveis;",
        "- identidade, conteúdo, datas, paginação, completude e traces comprovados;",
        "- bloqueios externos preservados sem false empty;",
        "- documentação e catálogos gerados em paridade;",
        "- scorecard revisado pelo papel de dados/QA;",
        "- evidência em verification.md do pacote de implementação;",
        "- fingerprint da evidência registrado e sem alteração pendente;",
        "- decisão final aceita, aceita com limitações, rejeitada, adiada com "
        "revisão ou fora de escopo;",
        "- produção e publicação somente com autorização humana.",
        "",
    ]
    return "\n".join(lines)


def build(root: Path, output_dir: Path) -> dict[str, Any]:
    catalog_path = root / "docs" / "registry" / "provider-catalog.full.json"
    catalog_payload = _read_json(catalog_path, {"entries": []})
    catalog = _entry_map(catalog_payload)
    offline_payload = audit_offline(root, catalog_path)
    offline = {str(row.get("source_id", "")): row for row in offline_payload.get("all_entries", [])}
    unified = _unified_map(
        _read_json(root / "docs" / "provider-discovery" / "unified-contract-matrix.json", {})
    )
    closure = _closure_map(
        _read_json(root / "docs" / "provider-discovery" / "provider-closure-ledger.json", {})
    )
    topology = packaged_topology()
    topology_bindings: dict[str, list[str]] = defaultdict(list)
    for collection in topology.collections:
        for source_id in collection.provider_ids:
            topology_bindings[source_id].append(collection.collection_id)

    previous_state = _read_json(output_dir / "execution-state.json", {"providers": {}})
    previous_providers = previous_state.get("providers", {})
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rows: list[dict[str, Any]] = []
    states: dict[str, Any] = {}
    workpack_dir = output_dir / "provider-workpacks"
    workpack_dir.mkdir(parents=True, exist_ok=True)

    for source in sorted(catalog):
        entry = catalog[source]
        offline_row = offline.get(source, {})
        unified_row = unified.get(source, {})
        closure_rows = closure.get(source, [])
        gaps = _gaps(entry, offline_row, unified_row, closure_rows)
        priority = _priority(entry, gaps)
        initial = _initial_status(entry, gaps)
        row = {
            "source_id": source,
            "display_name": entry.get("display_name", source),
            "implementation_status": entry.get("implementation_status", "unknown"),
            "coverage_role": entry.get("coverage_role", "unknown"),
            "maturity_tier": entry.get("maturity_tier", "unknown"),
            "maturity_score": (entry.get("maturity_score") or {}).get("total"),
            "target_tier": _target_tier(entry),
            "priority": priority,
            "gaps": gaps,
            "topology_collection_ids": topology_bindings.get(source, []),
            "workpack": f"provider-workpacks/{source}.md",
        }
        rows.append(row)
        state = dict(previous_providers.get(source, {}))
        legacy_status = str(state.get("status", ""))
        if legacy_status in LEGACY_STATUS_MIGRATIONS:
            migrated_status = LEGACY_STATUS_MIGRATIONS[legacy_status]
            state["status"] = migrated_status
            state["phase"] = "inspect" if migrated_status == "stale" else "research"
            conditions = list(state.get("blocking_conditions", []))
            conditions.append(
                {
                    "kind": "legacy_state_migrated",
                    "previous_status": legacy_status,
                    "current_status": migrated_status,
                    "resume_when": "review_under_provider_completion_state_v2",
                }
            )
            state["blocking_conditions"] = conditions
        fingerprint = evidence_fingerprint(row)
        previous_fingerprint = state.get("evidence_fingerprint")
        previous_status = str(state.get("status", initial))
        if (
            previous_fingerprint
            and previous_fingerprint != fingerprint
            and previous_status in TERMINAL_STATES
        ):
            state["status"] = "stale"
            state["phase"] = "inspect"
            conditions = list(state.get("blocking_conditions", []))
            conditions.append(
                {
                    "kind": "evidence_changed",
                    "previous_fingerprint": previous_fingerprint,
                    "current_fingerprint": fingerprint,
                    "resume_when": "revalidate_provider_evidence",
                }
            )
            state["blocking_conditions"] = conditions
        state.setdefault("status", initial)
        state.setdefault("phase", "inspect")
        state.setdefault("attempts", 0)
        state.setdefault("owner", None)
        state.setdefault("last_checkpoint", None)
        state.setdefault("blocking_conditions", [])
        state.setdefault("evidence", [])
        state.setdefault("operational_health", "not_checked")
        state.setdefault("disposition", None)
        state.setdefault("review_after", None)
        state.setdefault("resume_when", None)
        state["evidence_fingerprint"] = fingerprint
        state["priority"] = priority
        state["target_tier"] = row["target_tier"]
        state["topology_collection_ids"] = row["topology_collection_ids"]
        state["workpack"] = row["workpack"]
        states[source] = state
        (workpack_dir / f"{source}.md").write_text(
            _workpack(entry, offline_row, unified_row, closure_rows, gaps, state),
            encoding="utf-8",
        )

    rows.sort(key=lambda item: (item["priority"], item["source_id"]))
    baseline = {
        "schema_version": "provider-completion-baseline-v2",
        "generated_at": generated_at,
        "mode": "offline_only",
        "network_access": "not_used",
        "catalog": "docs/registry/provider-catalog.full.json",
        "summary": {
            "providers": len(rows),
            "runtime": sum(row["implementation_status"] == "runtime" for row in rows),
            "candidates": sum(row["implementation_status"] == "none" for row in rows),
            "families": sum(row["implementation_status"] == "family" for row in rows),
            "by_priority": dict(Counter(f"P{row['priority']}" for row in rows)),
            "by_target": dict(Counter(row["target_tier"] for row in rows)),
            "providers_with_gaps": sum(bool(row["gaps"]) for row in rows),
            "completion_dispositions": dict(
                Counter(str(state.get("disposition") or "pending") for state in states.values())
            ),
            "completion_statuses": dict(
                Counter(str(state.get("status") or "unknown") for state in states.values())
            ),
        },
        "topology": {
            "schema_version": topology.schema_version,
            "topology_version": topology.topology_version,
            "collections": len(topology.collections),
            "providers_reconciled": sum(bool(row["topology_collection_ids"]) for row in rows),
            "providers_unreconciled": sum(not bool(row["topology_collection_ids"]) for row in rows),
            "artifact": "docs/topology/national-topology.json",
        },
        "providers": rows,
    }
    state_payload = {
        "schema_version": "provider-completion-state-v2",
        "objective": (
            "Complete every provider to its evidence-based target or record a "
            "verified external blocker without masking it."
        ),
        "updated_at": generated_at,
        "terminal_states": sorted(TERMINAL_STATES),
        "providers": states,
    }
    # Completion runs are an execution-level audit record rather than a
    # provider field.  Preserve it across normal artifact regeneration so a
    # second generator pass cannot erase the bounded completion evidence.
    if previous_state.get("completion_run") is not None:
        state_payload["completion_run"] = previous_state["completion_run"]
    _write_json(output_dir / "provider-baseline.json", baseline)
    _write_json(output_dir / "execution-state.json", state_payload)
    (output_dir / "provider-completion-summary.md").write_text(
        _summary_markdown(baseline),
        encoding="utf-8",
    )
    return baseline


def _summary_markdown(baseline: dict[str, Any]) -> str:
    summary = baseline["summary"]
    rows = baseline["providers"]
    lines = [
        "# Resumo de conclusão dos providers",
        "",
        f"Gerado em: {baseline['generated_at']}",
        "Modo: offline_only; nenhuma fonte externa foi chamada.",
        "",
        "## Escopo",
        "",
        f"- fontes: {summary['providers']}",
        f"- runtime: {summary['runtime']}",
        f"- candidates: {summary['candidates']}",
        f"- famílias: {summary['families']}",
        f"- fontes com lacunas automáticas: {summary['providers_with_gaps']}",
        "",
        "## Fechamento das unidades",
        "",
        "As tarefas WP representam processamento de decisão. Evidência ausente",
        "permanece em lacunas, limitações e condições de retomada; não é convertida",
        "em sucesso implícito.",
        "",
        "- disposições: "
        + ", ".join(
            f"{key}={value}"
            for key, value in sorted(summary.get("completion_dispositions", {}).items())
        ),
        "- estados: "
        + ", ".join(
            f"{key}={value}"
            for key, value in sorted(summary.get("completion_statuses", {}).items())
        ),
        "",
        "## Topologia reconciliada",
        "",
        f"- versão: {baseline.get('topology', {}).get('topology_version', 'unknown')}",
        f"- collections: {baseline.get('topology', {}).get('collections', 0)}",
        f"- providers reconciliados: {baseline.get('topology', {}).get('providers_reconciled', 0)}",
        f"- providers sem vínculo: {baseline.get('topology', {}).get('providers_unreconciled', 0)}",
        "- vínculos desconhecidos permanecem explícitos e não são prova de cobertura.",
        "",
        "## Fila",
        "",
        "| Prioridade | Source | Lifecycle | Role | Maturity | Target | Gaps |",
        "| --- | --- | --- | --- | --- | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| P{row['priority']} | [{row['source_id']}]"
            f"(provider-workpacks/{row['source_id']}.md) | "
            f"{row['implementation_status']} | {row['coverage_role']} | "
            f"{row['maturity_tier']} | {row['target_tier']} | {len(row['gaps'])} |"
        )
    lines += [
        "",
        "## Interpretação",
        "",
        "- P0: jurisprudência textual com bloqueio, bronze ou fixture insuficiente.",
        "- P1: jurisprudência textual runtime ainda abaixo de gold.",
        "- P2: jurisprudência textual gold que requer revisão de fechamento.",
        "- P3: fontes contextuais runtime.",
        "- P4: candidates sem runtime.",
        "- P5: família técnica não executável isoladamente.",
        "",
        "A fila orienta trabalho; não promove provider e não substitui revisão humana.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    root = args.root.resolve()
    output = (
        args.output_dir.resolve()
        if args.output_dir.is_absolute()
        else (root / args.output_dir).resolve()
    )
    baseline = build(root, output)
    print(json.dumps(baseline["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
