"""Build an evidence ledger for discovery TODO closure.

The ledger makes the distinction between a locally proven contract, an
external operational block and work that still needs new evidence. It never
silences a TODO merely because a route was observed in HTML.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = str(ROOT / "src")
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)

OUTPUT_DIR = ROOT / "docs" / "provider-discovery"
SWEEP_PATH = OUTPUT_DIR / "all-provider-sweep.json"
REGISTRY_PATH = ROOT / "docs" / "registry" / "providers.json"
PROMOTION_MANIFEST_PATH = (
    ROOT / "docs" / "operations" / "technical-promotion-manifest-20260905.json"
)
CATALOG_PATH = ROOT / "docs" / "registry" / "provider-catalog.full.json"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    except OSError:
        return ""


def _registered_runtime_sources() -> set[str]:
    """Return the registry's runtime sources for stale discovery snapshots.

    The bounded discovery snapshot is intentionally immutable evidence.  When
    a candidate is promoted later, the snapshot still contains its old
    ``catalog_candidates`` row.  Reconcile that row with the source registry
    instead of regressing the closure ledger to ``candidate``.
    """
    try:
        payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {str(source) for source in payload.get("implemented", [])}


def _local_evidence(source: str) -> dict[str, Any]:
    module = ROOT / "src" / "nanojuris" / "providers" / f"{source}.py"
    dossier = ROOT / "docs" / "providers" / source / "README.md"
    contract = ROOT / "docs" / "source-contracts" / f"{source}.md"
    test_paths = sorted((ROOT / "tests").glob(f"test_{source}*.py"))
    # Shared provider families (notably eproc) keep their implementation and
    # tests in one module. Include only files that explicitly name the source.
    for path in sorted((ROOT / "src" / "nanojuris" / "providers").glob("*.py")):
        if path.name != "__init__.py" and source in _read(path) and path != module:
            module = path
            break
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        if path not in test_paths and source in _read(path):
            test_paths.append(path)
    test_paths = sorted(test_paths)
    fixture_paths = sorted((ROOT / "tests" / "fixtures").glob(f"*{source}*"))
    state_fixture = ROOT / "tests" / "fixtures" / "provider_contracts.json"
    if source in _read(state_fixture):
        fixture_paths.append(state_fixture)
    texts = {
        "module": _read(module),
        "dossier": _read(dossier),
        "contract": _read(contract),
        "tests": "\n".join(_read(path) for path in test_paths),
        "fixtures": "\n".join(_read(path) for path in fixture_paths),
    }
    # Many provider tests use a short source alias (for example `bnp` for
    # `bnp_pangea`). Resolve those explicit fixture references as evidence
    # without broadening the fixture glob heuristically.
    referenced_fixture_paths: list[Path] = []
    for match in re.findall(r"[\"']([^\"']+\.(?:json|html|csv|txt))[\"']", texts["tests"], re.I):
        candidate = ROOT / "tests" / "fixtures" / Path(match).name
        if candidate.is_file() and candidate not in fixture_paths:
            referenced_fixture_paths.append(candidate)
    fixture_paths = sorted({*fixture_paths, *referenced_fixture_paths})
    texts["fixtures"] = "\n".join(_read(path) for path in fixture_paths)
    has_inline_fixtures = bool(
        re.search(r"(?:_HTML|_JSON|_CSV|FIXTURE|FakeResponse|fixture)", texts["tests"], re.I)
    )
    return {
        "paths": [
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in [module, dossier, contract, *test_paths, *fixture_paths]
            if path.is_file()
        ],
        "texts": texts,
        "has_tests": bool(test_paths),
        "has_fixtures": bool(fixture_paths),
        "has_inline_fixtures": has_inline_fixtures,
    }


def _status_set(row: dict[str, Any]) -> set[str]:
    statuses = set((row.get("metrics") or {}).get("statuses", {}))
    for observation in row.get("observations", []):
        if observation.get("status"):
            statuses.add(str(observation["status"]))
    return statuses


@lru_cache(maxsize=1)
def _catalog_blocked_sources() -> frozenset[str]:
    """Return candidates whose current catalog status is externally blocked.

    Discovery snapshots can predate a focused access-control check.  Reading
    the generated catalog here prevents a candidate with local code/fixtures
    from being mislabeled as merely awaiting promotion when its public route
    is currently blocked.
    """

    try:
        payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return frozenset()
    blocked = {
        "access_controlled",
        "blocked_access",
        "blocked_access_control_no_reproducible_result",
        "blocked_transport",
        "source_unavailable",
        "transport_blocked",
        "unavailable",
    }
    return frozenset(
        str(entry.get("source_id"))
        for entry in payload.get("entries", [])
        if isinstance(entry, dict)
        and entry.get("source_id")
        and str(entry.get("live_status")) in blocked
    )


@lru_cache(maxsize=1)
def _current_live_valid_sources() -> frozenset[str]:
    """Return sources with a newer valid live observation.

    The discovery sweep is an immutable historical snapshot and can retain an
    old WAF/CAPTCHA signal after a later bounded check succeeds.  Reconcile
    that stale signal with the promotion manifest when building the closure
    ledger; the historical evidence remains attached to the item.
    """

    try:
        payload = json.loads(PROMOTION_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return frozenset()
    return frozenset(
        str(row.get("source"))
        for row in payload.get("decisions", [])
        if isinstance(row, dict)
        and row.get("mode") == "enabled"
        and row.get("live_status") == "valid"
    )


def _classify_todo(
    source: str,
    todo: str,
    row: dict[str, Any],
    local: dict[str, Any],
    *,
    candidate: bool = False,
) -> dict[str, Any]:
    evidence = list(local["paths"])
    statuses = _status_set(row)
    current_live_valid = source in _current_live_valid_sources()
    if candidate:
        # Access/transport failures take precedence over local adapter
        # completeness.  A diagnostic adapter can have tests and fixtures and
        # still be ineligible for promotion while its source is blocked.
        blocked_markers = statuses.intersection(
            {
                "robots_disallowed",
                "access_controlled",
                "blocked_access",
                "blocked_access_control_no_reproducible_result",
                "blocked_transport",
                "request_blocked",
                "source_unavailable",
                "timeout",
                "tls_error",
                "transport_blocked",
                "unavailable",
            }
        )
        if source in _catalog_blocked_sources():
            blocked_markers.add("catalog_live_status")
        if blocked_markers and not current_live_valid:
            return {
                "status": "blocked_external",
                "evidence": evidence
                + ["candidate access/transport state: " + ", ".join(sorted(blocked_markers))],
                "next_action": (
                    "aguardar rota pÃºblica oficial reproduzÃ­vel ou alteraÃ§Ã£o observÃ¡vel "
                    "da polÃ­tica de acesso antes de promover"
                ),
            }
        # Discovery snapshots can lag behind an adapter that was implemented
        # through a separate SDD.  Keep it candidate-only for runtime
        # purposes, but do not mislabel its code and fixtures as absent.
        has_runtime_module = any(
            path.startswith("src/nanojuris/providers/") for path in local["paths"]
        )
        if (
            has_runtime_module
            and local["has_tests"]
            and (local["has_fixtures"] or local["has_inline_fixtures"])
        ):
            return {
                "status": "candidate_pending_promotion",
                "evidence": evidence
                + [
                    "runtime adapter + provider tests + fixtures",
                    "explicit opt-in only; default federation unchanged",
                ],
                "next_action": (
                    "fechar contrato live, reuso/licenca e revisao humana antes da promocao"
                ),
            }
        return {
            "status": "candidate_pending_adapter",
            "evidence": local["paths"] or ["docs/provider-discovery/all-provider-sweep.json"],
            "next_action": "aprovar contrato, fixtures de sucesso/vazio/erro e parser antes do adapter",
        }

    texts = local["texts"]
    combined = "\n".join(texts.values()).lower()
    if current_live_valid and any(
        marker in todo.lower()
        for marker in ("robots.txt", "controle de acesso", "indisponibilidade")
    ):
        return {
            "status": "implemented_with_local_evidence",
            "evidence": evidence + ["latest promotion manifest reports a valid bounded live check"],
            "next_action": (
                "manter o diagnostico historico e repetir o smoke bounded quando a fonte mudar"
            ),
        }
    # Candidate snapshots predate adapter promotion.  Once the source has a
    # runtime module, versioned fixtures and tests, close the stale generic
    # adapter TODO with the current local contract evidence.
    if (
        "criar adapter" in todo.lower()
        and local["has_tests"]
        and (local["has_fixtures"] or local["has_inline_fixtures"])
    ):
        return {
            "status": "implemented_with_local_evidence",
            "evidence": evidence + ["runtime adapter + provider tests + fixtures"],
            "next_action": "manter o escopo promovido e ampliar somente com novo contrato reproduzivel",
        }
    if "confirmar rotas, filtros, paginação e detalhe" in todo.lower() and local["has_tests"]:
        return {
            "status": "implemented_with_local_evidence",
            "evidence": evidence + ["runtime contract documented in module/docs/tests"],
            "next_action": "preservar limites declarados; promover busca decisoria somente com contrato de resultados",
        }

    if "robots.txt" in todo.lower() and "robots_disallowed" in statuses and not current_live_valid:
        return {
            "status": "blocked_external",
            "evidence": evidence
            + ["docs/provider-discovery/all-provider-sweep.json#robots_disallowed"],
            "next_action": "revalidar somente após alteração autorizada da política pública/robots",
        }
    if (
        "controle de acesso" in todo.lower()
        and statuses.intersection(
            {"access_controlled", "login_required", "redirect_outside_allowlist"}
        )
        and not current_live_valid
    ):
        return {
            "status": "blocked_external",
            "evidence": evidence
            + ["docs/provider-discovery/all-provider-sweep.json#access_controlled"],
            "next_action": "usar rota pública alternativa documentada ou aguardar acesso autorizado",
        }
    if (
        "indisponibilidade" in todo.lower()
        and statuses.intersection({"source_unavailable", "timeout", "tls_error"})
        and not current_live_valid
    ):
        return {
            "status": "blocked_external",
            "evidence": evidence
            + ["docs/provider-discovery/all-provider-sweep.json#source_unavailable"],
            "next_action": "retestar em janela autorizada e preservar diagnóstico de falha",
        }
    if "sinais de jurisprudência" in todo.lower():
        declared = row.get("declared") or {}
        if declared.get("canonical_records") and declared.get("extracted_fields"):
            return {
                "status": "implemented_with_local_evidence",
                "evidence": evidence + ["ProviderCapabilities.canonical_records/extracted_fields"],
                "next_action": "manter fixture live/replay quando a fonte mudar",
            }
    if "GETs declarados" in todo:
        comparison = row.get("contract_comparison") or {}
        unobserved = comparison.get("unobserved_declared_get_routes") or []
        if (
            unobserved
            and local["has_tests"]
            and (
                "get_document" in combined
                or any(
                    route.get("declaration", "").split("/")[-1].lower() in combined
                    for route in unobserved
                )
            )
        ):
            return {
                "status": "implemented_with_local_evidence",
                "evidence": evidence + ["declared route referenced by module/docs/tests"],
                "next_action": "replay local e promover observação live quando a fonte permitir",
            }
    if "payload" in todo.lower() and "post" in todo.lower():
        if "post" in combined and local["has_tests"] and local["has_fixtures"]:
            return {
                "status": "implemented_with_local_evidence",
                "evidence": evidence + ["POST implementation + provider test + fixture"],
                "next_action": "não submeter payload especulativo; revalidar por replay/contrato aprovado",
            }
    if (
        "fixture" in todo.lower()
        and local["has_tests"]
        and (local["has_fixtures"] or local["has_inline_fixtures"])
    ):
        return {
            "status": "implemented_with_local_evidence",
            "evidence": evidence + ["provider tests and versioned fixture"],
            "next_action": "expandir estados somente se o contrato da fonte mudar",
        }

    return {
        "status": "needs_new_evidence",
        "evidence": evidence,
        "next_action": "obter contrato público/replay aprovado e adicionar fixture antes de alterar o adapter",
    }


def build_ledger(payload: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    runtime_sources = _registered_runtime_sources()
    for provider in payload.get("providers", []):
        source = provider.get("source", "")
        local = _local_evidence(source)
        for todo in provider.get("todo", []):
            closure = _classify_todo(source, todo, provider, local)
            rows.append({"source": source, "kind": "runtime", "todo": todo, **closure})
    for candidate in payload.get("catalog_candidates", []):
        source = candidate.get("source", "")
        local = _local_evidence(source)
        for todo in candidate.get("todo", []):
            promoted = source in runtime_sources
            closure = _classify_todo(
                source,
                todo,
                candidate,
                local,
                candidate=not promoted,
            )
            rows.append(
                {
                    "source": source,
                    "kind": "runtime" if promoted else "candidate",
                    "todo": todo,
                    **closure,
                }
            )
    from collections import Counter

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "discovery_generated_at": payload.get("generated_at"),
        "discovery_mode": payload.get("mode"),
        "summary": {
            "items": len(rows),
            "by_status": dict(Counter(row["status"] for row in rows)),
            "runtime_items": sum(row["kind"] == "runtime" for row in rows),
            "candidate_items": sum(row["kind"] == "candidate" for row in rows),
        },
        "items": rows,
    }


def render_markdown(ledger: dict[str, Any]) -> str:
    summary = ledger["summary"]
    lines = [
        "# Ledger de fechamento de TODOs dos providers",
        "",
        f"Gerado em `{ledger['generated_at']}`; discovery `{ledger.get('discovery_generated_at')}`.",
        "",
        f"Itens: **{summary['items']}**; runtime: **{summary['runtime_items']}**; candidates: **{summary['candidate_items']}**.",
        f"Estados: `{json.dumps(summary['by_status'], ensure_ascii=False)}`.",
        "",
        "`implemented_with_local_evidence` encerra o trabalho de implementação somente com evidência local versionada; `blocked_external` permanece visível e não equivale a sucesso; `needs_new_evidence` exige trabalho adicional.",
        "",
        "| Source | Tipo | Estado | TODO | Evidência | Próxima ação |",
        "|---|---|---|---|---|---|",
    ]
    for item in ledger["items"]:
        evidence = "; ".join(item["evidence"][:3]) or "-"
        lines.append(
            f"| `{item['source']}` | {item['kind']} | `{item['status']}` | {item['todo']} | {evidence} | {item['next_action']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep", type=Path, default=SWEEP_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    payload = json.loads(args.sweep.read_text(encoding="utf-8"))
    ledger = build_ledger(payload)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "provider-closure-ledger.json").write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "provider-closure-ledger.md").write_text(
        render_markdown(ledger), encoding="utf-8"
    )
    print(json.dumps(ledger["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
