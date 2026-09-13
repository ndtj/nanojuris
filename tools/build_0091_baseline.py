"""Build the hash-bound baseline for SDD 0091 without network access."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_0091_local_gates import build as build_gate_audit  # noqa: E402

HANDOFF = ROOT / "specs" / "changes" / "0091-national-coverage-gold-handoff"
OUTPUT = HANDOFF / "baseline-20260908.json"


def build(root: Path = ROOT) -> dict[str, Any]:
    audit = build_gate_audit(root)
    summary = audit["summary"]
    values = {
        "documented_sources": summary["catalog_entries"],
        "runtime_providers": summary["runtime_entries"],
        "registered_runtime_providers": summary["registered_entries"],
        "unified_sources_declared": _read_unified_count(root),
        "state_appellate_complete": _read_degree_count(root, "CJSG"),
        "state_appellate_authorities": 27,
        "cjpg_proven": _read_degree_count(root, "CJPG"),
        "cjsg_proven": _read_degree_count(root, "CJSG"),
        "fixture_complete_runtime": summary["fixture_summary"]["complete"],
        "open_tasks": summary["open_tasks"],
        "local_open_tasks": summary["open_task_classification"].get("local_evidence", 0),
        "external_open_tasks": summary["open_task_classification"].get("external_source", 0),
        "human_open_tasks": summary["open_task_classification"].get("human_review", 0),
    }
    return {
        "schema_version": "1.2",
        "kind": "handoff_baseline_reference",
        "observed_at": "2026-09-08",
        "repository": "repos/nanojuris",
        "values": values,
        "local_gate_audit": {
            "artifact": "docs/coverage/0091-local-gates-20260908.json",
            "passed": summary["passed"],
            "pending": summary["pending"],
        },
        "artifact_sha256": audit["artifact_sha256"],
        "status": "locally_verified_with_external_pending",
        "regenerate_with": [
            "python tools/audit_open_tasks.py",
            "python tools/build_provider_coverage.py --write",
            "python tools/build_degree_coverage.py",
            "python tools/build_surface_state_registry.py",
            "python tools/build_state_appellate_program.py --write",
            "python tools/build_promotion_manifest.py --write",
            "python tools/build_fixture_completeness.py --write",
            "python tools/audit_0091_local_gates.py --write",
            "python tools/build_0091_baseline.py --write",
        ],
        "warning": (
            "These values prove repository consistency only, not national availability "
            "or legal approval."
        ),
    }


def _read_unified_count(root: Path) -> int:
    payload = json.loads(
        (root / "docs" / "registry" / "provider-catalog.full.json").read_text(encoding="utf-8")
    )
    return int(payload["summary"]["unified_search_sources"])


def _read_degree_count(root: Path, key: str) -> str:
    payload = json.loads(
        (root / "docs" / "topology" / "degree-coverage-matrix-20260901.json").read_text(
            encoding="utf-8"
        )
    )
    row = payload["summary"]["by_collection"][key]
    return f"{row['implemented']}/{row['expected']}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    payload = build(args.root.resolve())
    output = args.root.resolve() / OUTPUT.relative_to(ROOT)
    if args.write:
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(payload["values"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
