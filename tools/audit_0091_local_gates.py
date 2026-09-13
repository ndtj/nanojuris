"""Audit locally reproducible gates for the national coverage handoff.

This tool is intentionally conservative.  It checks only repository-local
artifacts and source contracts; it never treats an adapter, an HTTP 200, or a
generated count as proof of live availability.  External-source and human
approval tasks remain pending until their evidence is recorded separately.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "specs" / "changes" / "0091-national-coverage-gold-handoff"
CATALOG = ROOT / "docs" / "registry" / "provider-catalog.full.json"
RUNTIME = ROOT / "docs" / "registry" / "providers.json"
SURFACES = ROOT / "docs" / "coverage" / "surface-state-registry-20260902.json"
FIXTURES = ROOT / "docs" / "coverage" / "fixture-completeness-20260908.json"
PROMOTION = ROOT / "docs" / "operations" / "technical-promotion-manifest-20260905.json"
OPEN_TASKS = ROOT / "docs" / "coverage" / "open-task-audit-current.json"
JUSCRAPER = ROOT.parent / ".tmp-juscraper"

REQUIRED_HANDOFF_FILES = (
    "spec-of-specs.md",
    "spec.md",
    "design.md",
    "implementation-plan.md",
    "clarify.md",
    "research.md",
    "traceability.md",
    "tasks.md",
    "verification.md",
    "threat-model.md",
    "provider-workpack-template.md",
    "lawful-access-decision-matrix.md",
    "model-runbook.md",
    "execution-manifest.json",
    "evidence-record.schema.json",
    "promotion-gate.schema.json",
    "human-decision-record.template.json",
    "GOAT_EXECUTOR_PROMPT.md",
    "MODEL_HANDOFF.md",
    "model-handoff-status.json",
    "handoff-artifact-manifest.json",
    "CONTINUATION_BRIEF.md",
)

KEY_ARTIFACTS = (
    CATALOG,
    RUNTIME,
    SURFACES,
    FIXTURES,
    PROMOTION,
    OPEN_TASKS,
    ROOT / "docs" / "coverage" / "open-task-audit-20260907.json",
    ROOT / "docs" / "coverage" / "national-coverage-gold-handoff-20260908.json",
    ROOT / "docs" / "coverage" / "national-coverage-model-handoff-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjmg-modern-api-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjma-informativos-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "stm-live-20260908-cycle70.json",
    ROOT / "docs" / "provider-discovery" / "trf4-live-20260908-cycle71.json",
    ROOT / "docs" / "provider-discovery" / "trf4-second-degree-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "federal-eproc-degree-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "trf5-live-20260908-cycle72.json",
    ROOT / "docs" / "provider-discovery" / "eproc-detail-live-20260908-cycle73.json",
    ROOT / "docs" / "provider-discovery" / "stj-live-20260908-cycle74.json",
    ROOT / "docs" / "provider-discovery" / "eproc-detail-live-20260908-cycle75.json",
    ROOT / "docs" / "provider-discovery" / "tjrj-banco-sentencas-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjba-cjpg-banco-sentencas-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "tjpa-banco-sentencas-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "first-degree-secondary-probes-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "trf3-exact-process-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjal-turma-recursal-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle77.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-optin-live-20260908-cycle78.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle79.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle80.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle81.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle82.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle83.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle84.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle85.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle87.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle88.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle89.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle90.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle91.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle92.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle93.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle94.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle95.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle96.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle97.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle98.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260908-cycle100.json",
    ROOT / "docs" / "provider-discovery" / "tjpr-sentenca-digital-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjma-jurisprudence-route-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjsc-eproc-cjpg-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjrs-sentencas-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "trt2-jurisprudencia-api-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "trt3-jurisprudencia-route-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "trt4-jurisprudencia-route-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tre-sjur-route-inventory-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tre-sjur-gold-live-20260909.json",
    ROOT / "docs" / "coverage" / "0091-artifact-audit-20260908.json",
    HANDOFF / "surface-workpacks" / "manifest.json",
)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(name: str, passed: bool, evidence: list[str], note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "status": "passed" if passed else "pending",
        "evidence": evidence,
        "note": note,
    }


def build(root: Path = ROOT) -> dict[str, Any]:
    catalog = _read(root / CATALOG.relative_to(ROOT))
    runtime = _read(root / RUNTIME.relative_to(ROOT))
    surfaces = _read(root / SURFACES.relative_to(ROOT))
    fixtures = _read(root / FIXTURES.relative_to(ROOT))
    promotion = _read(root / PROMOTION.relative_to(ROOT))
    tasks = _read(root / OPEN_TASKS.relative_to(ROOT))
    entries = list(catalog.get("entries", []))
    ids = [str(row.get("source_id")) for row in entries if row.get("source_id")]
    runtime_ids = {
        str(row.get("source_id"))
        for row in entries
        if row.get("implementation_status") == "runtime" and row.get("source_id")
    }
    registered_ids = {str(value) for value in runtime.get("implemented", []) if value}
    registered_ids.update(
        str(row.get("source"))
        for row in runtime.get("providers", runtime.get("entries", []))
        if isinstance(row, dict) and row.get("source")
    )
    if not registered_ids:
        registered_ids = {
            str(row.get("source_id"))
            for row in runtime.get("entries", [])
            if isinstance(row, dict) and row.get("source_id")
        }

    local_checks = [
        _check(
            "handoff_artifacts",
            all(
                (root / HANDOFF.relative_to(ROOT) / name).is_file()
                for name in REQUIRED_HANDOFF_FILES
            ),
            [
                f"specs/changes/0091-national-coverage-gold-handoff/{name}"
                for name in REQUIRED_HANDOFF_FILES
            ],
        ),
        _check(
            "generated_inventory_set",
            all(path.is_file() for path in KEY_ARTIFACTS),
            [str(path.relative_to(root)).replace("\\", "/") for path in KEY_ARTIFACTS],
        ),
        _check(
            "catalog_identity_fields",
            bool(ids)
            and len(ids) == len(set(ids))
            and all(
                row.get("source_id")
                and row.get("identity")
                and row.get("implementation_status")
                and row.get("lifecycle")
                and row.get("maturity_tier")
                and row.get("live_status")
                for row in entries
            ),
            ["docs/registry/provider-catalog.full.json"],
            "Owner/TTL/evidence completeness is audited separately and is not inferred here.",
        ),
        _check(
            "runtime_catalog_reconciliation",
            runtime_ids == registered_ids if registered_ids else False,
            ["docs/registry/provider-catalog.full.json", "docs/registry/providers.json"],
            f"runtime_catalog={len(runtime_ids)} registered={len(registered_ids)}",
        ),
        _check(
            "fixture_gate",
            fixtures.get("summary", {}).get("incomplete") == 0
            and fixtures.get("summary", {}).get("complete")
            == fixtures.get("summary", {}).get("runtime_providers"),
            ["docs/coverage/fixture-completeness-20260908.json"],
        ),
        _check(
            "surface_state_shape",
            bool(surfaces.get("surfaces"))
            and all(
                all(
                    key in row
                    for key in (
                        "authority",
                        "branch",
                        "degree",
                        "collection",
                        "provider",
                        "lifecycle",
                        "live_status",
                        "contract_status",
                        "federation_status",
                    )
                )
                for row in surfaces.get("surfaces", [])
            ),
            ["docs/coverage/surface-state-registry-20260902.json"],
        ),
        _check(
            "technical_promotion_manifest",
            promotion.get("schema_version") is not None
            and isinstance(promotion.get("decisions"), list),
            ["docs/coverage/technical-promotion-manifest-20260905.json"],
            "Technical promotion is not legal approval.",
        ),
        _check(
            "open_task_classification",
            set(tasks.get("by_classification", {}))
            <= {"local_evidence", "external_source", "human_review"},
            ["docs/coverage/open-task-audit-current.json"],
            "External-source and human-review tasks remain open by policy.",
        ),
        _check(
            "juscraper_pinned_reference",
            (root.parent / ".tmp-juscraper" / ".git" / "HEAD").is_file()
            and any(
                (root.parent / ".tmp-juscraper" / name).is_file()
                for name in ("LICENSE", "COPYING", "pyproject.toml")
            ),
            ["../.tmp-juscraper/.git/HEAD", "../.tmp-juscraper/LICENSE or pyproject.toml"],
            "Reference-only; no third-party code is copied by this audit.",
        ),
        _check(
            "modern_tjmg_live_evidence",
            (root / "docs/provider-discovery/tjmg-modern-api-live-20260908.json").is_file()
            and _read(root / "docs/provider-discovery/tjmg-modern-api-live-20260908.json").get(
                "bypass_used"
            )
            is False,
            ["docs/provider-discovery/tjmg-modern-api-live-20260908.json"],
            "Bounded public evidence; not a claim of permanent availability.",
        ),
    ]
    hashes = {
        str(path.relative_to(root)).replace("\\", "/"): _sha256(path) for path in KEY_ARTIFACTS
    }
    summary = {
        "passed": sum(row["status"] == "passed" for row in local_checks),
        "pending": sum(row["status"] == "pending" for row in local_checks),
        "catalog_entries": len(entries),
        "runtime_entries": len(runtime_ids),
        "registered_entries": len(registered_ids),
        "open_tasks": tasks.get("open_tasks"),
        "open_task_classification": tasks.get("by_classification", {}),
        "fixture_summary": fixtures.get("summary", {}),
    }
    pending = summary["pending"]
    next_action = (
        "Resolve pending local checks, then process external and human tasks with evidence."
        if pending
        else "Process external and human tasks with evidence; no local gate remains pending."
    )
    return {
        "schema_version": "0091-local-gates-v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "policy": {
            "network_used": False,
            "external_and_human_tasks_not_fabricated": True,
            "no_bypass": True,
            "no_release": True,
        },
        "summary": summary,
        "checks": local_checks,
        "artifact_sha256": hashes,
        "next_action": next_action,
    }


def render(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# 0091 local gate audit",
        "",
        "Auditoria offline e conservadora; não substitui live checks nem aprovação humana.",
        "",
        f"- Gates locais aprovados: **{summary['passed']}**",
        f"- Gates locais pendentes: **{summary['pending']}**",
        f"- Providers catalogados/runtime/registrados: **{summary['catalog_entries']} / "
        f"{summary['runtime_entries']} / {summary['registered_entries']}**",
        f"- Tarefas abertas: **{summary['open_tasks']}** ({summary['open_task_classification']})",
        "",
        "| Gate | Estado | Evidência | Nota |",
        "|---|---|---|---|",
    ]
    for check in payload["checks"]:
        evidence = ", ".join(f"`{item}`" for item in check["evidence"])
        lines.append(
            f"| `{check['name']}` | **{check['status']}** | {evidence} | {check['note']} |"
        )
    lines.extend(
        [
            "",
            "Os hashes dos artefatos estão no JSON para o próximo executor comparar",
            "alterações entre lotes. Nenhum commit, push, deploy ou alteração de produção "
            "foi realizado.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "docs/coverage/0091-local-gates-20260908.json"
    )
    parser.add_argument(
        "--markdown-output", type=Path, default=ROOT / "docs/coverage/0091-local-gates-20260908.md"
    )
    args = parser.parse_args()
    payload = build(ROOT)
    if args.write:
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        args.markdown_output.write_text(render(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0 if payload["summary"]["pending"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
