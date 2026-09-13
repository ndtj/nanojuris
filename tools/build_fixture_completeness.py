"""Build the runtime fixture-completeness gate from local evidence only."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs/registry/provider-catalog.full.json"
OFFLINE_AUDIT = ROOT / "docs/provider-discovery/offline-audit.json"
SHARED_FIXTURE = ROOT / "tests/fixtures/provider_runtime_scenarios.json"
DEFAULT_OUTPUT = ROOT / "docs/coverage/fixture-completeness-20260908.json"
DEFAULT_MARKDOWN = ROOT / "docs/coverage/fixture-completeness-20260908.md"

REMOTE_PAGINATION = {
    "page",
    "offset",
    "cursor",
    "livewire_page",
    "merged_collection_page",
    "dspace_page",
    "edition_section",
    "detail_links",
    "catalog_offset",
}
REQUIRED_SCENARIOS = {
    "success",
    "authoritative_empty",
    "external_failure",
    "schema_invalid",
    "second_page",
}


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_fixture_scenarios(names: list[str]) -> set[str]:
    scenarios: set[str] = set()
    for name in names:
        lowered = name.casefold()
        if any(
            marker in lowered
            for marker in (
                "success",
                "result",
                "search",
                "detail",
                "rows",
                "document",
                "index",
                "form",
                "topic",
                "catalog",
                "species",
                "manifest",
            )
        ):
            scenarios.add("success")
        if any(marker in lowered for marker in ("empty", "no_result", "no-results")):
            scenarios.add("authoritative_empty")
        if any(
            marker in lowered
            for marker in ("invalid", "error", "blocked", "access", "waf", "contract_changed")
        ):
            scenarios.add("external_failure")
        if any(
            marker in lowered for marker in ("schema_drift", "schema_changed", "contract_changed")
        ):
            scenarios.add("schema_invalid")
        if any(marker in lowered for marker in ("page2", "pagination", "second")):
            scenarios.add("second_page")
    return scenarios


def _test_has_second_page(root: Path, paths: list[str]) -> bool:
    pattern = re.compile(r"page\s*=\s*2|page_number\s*=\s*2|next_page\s*=\s*2|page2", re.I)
    return any(
        pattern.search((root / path).read_text(encoding="utf-8", errors="replace"))
        for path in paths
    )


def build(
    catalog_payload: dict[str, Any], audit_payload: dict[str, Any], shared: dict[str, Any]
) -> dict[str, Any]:
    runtime = [
        row
        for row in catalog_payload.get("entries", [])
        if row.get("implementation_status") == "runtime"
    ]
    offline = {str(row["source_id"]): row for row in audit_payload.get("all_entries", [])}
    shared_scenarios = set(shared.get("scenarios", {}))
    if shared_scenarios != REQUIRED_SCENARIOS:
        raise ValueError(f"shared scenario envelope mismatch: {sorted(shared_scenarios)}")

    providers: list[dict[str, Any]] = []
    for entry in sorted(runtime, key=lambda row: str(row.get("source_id"))):
        source = str(entry["source_id"])
        evidence = offline.get(source, {})
        names = [str(value) for value in evidence.get("fixture_references", [])]
        tests = [str(value) for value in evidence.get("test_references", [])]
        specific = _source_fixture_scenarios(names)
        mode = str((entry.get("pagination_contract") or {}).get("mode", "unknown"))
        second_page_applicable = mode in REMOTE_PAGINATION
        if _test_has_second_page(ROOT, tests):
            specific.add("second_page")
        required = set(REQUIRED_SCENARIOS)
        if not second_page_applicable:
            required.remove("second_page")
        providers.append(
            {
                "source": source,
                "pagination_mode": mode,
                "second_page_applicable": second_page_applicable,
                "fixture_references": names,
                "test_references": tests,
                "source_specific_scenarios": sorted(specific),
                "shared_scenarios": sorted(shared_scenarios),
                "required_scenarios": sorted(required),
                "source_fixture_present": bool(names),
                "complete": bool(names) and required <= shared_scenarios,
                "evidence_mode": "source_plus_shared_contract" if names else "shared_only",
            }
        )

    incomplete = [row["source"] for row in providers if not row["complete"]]
    return {
        "schema_version": "fixture-completeness-v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "policy": {
            "network_used": False,
            "shared_contract_scenarios_are_not_source_responses": True,
            "source_fixture_required": True,
            "non_applicable_second_page_allowed": True,
        },
        "summary": {
            "runtime_providers": len(providers),
            "complete": len(providers) - len(incomplete),
            "incomplete": len(incomplete),
            "source_fixture_evidence": sum(row["source_fixture_present"] for row in providers),
            "second_page_applicable": sum(row["second_page_applicable"] for row in providers),
            "incomplete_sources": incomplete,
        },
        "shared_scenarios": sorted(shared_scenarios),
        "providers": providers,
        "source_files": [
            str(CATALOG.relative_to(ROOT)),
            str(OFFLINE_AUDIT.relative_to(ROOT)),
            str(SHARED_FIXTURE.relative_to(ROOT)),
        ],
    }


def render(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Fixture completeness gate",
        "",
        "Gerado offline por `tools/build_fixture_completeness.py`.",
        "",
        f"- Providers runtime: **{summary['runtime_providers']}**",
        f"- Completos no envelope de cenários: **{summary['complete']}**",
        f"- Incompletos: **{summary['incomplete']}**",
        f"- Com fixture específica versionada: **{summary['source_fixture_evidence']}**",
        f"- Com segunda página aplicável: **{summary['second_page_applicable']}**",
        "",
        "A matriz combina fixture específica de cada provider com o envelope"
        " canônico compartilhado. O envelope não é resposta de tribunal: ele"
        " valida distinção de estados no transporte e na federação.",
        "",
        "| Provider | Paginação | Fixture específica | Segunda página "
        "aplicável | Evidência | Estado |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in payload["providers"]:
        lines.append(
            f"| `{row['source']}` | `{row['pagination_mode']}` | "
            f"{str(row['source_fixture_present']).lower()} | "
            f"{str(row['second_page_applicable']).lower()} | `{row['evidence_mode']}` | "
            f"{'complete' if row['complete'] else 'incomplete'} |"
        )
    lines.extend(["", "Nenhum corpo de fonte foi obtido pela geração deste artefato.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    payload = build(_read(CATALOG), _read(OFFLINE_AUDIT), _read(SHARED_FIXTURE))
    if args.write:
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        args.markdown_output.write_text(render(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0 if payload["summary"]["incomplete"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
