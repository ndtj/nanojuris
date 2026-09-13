"""Validate that the follow-up executor packet matches the current task audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_open_tasks import build_report  # noqa: E402

DEFAULT_PACKET = ROOT / "docs" / "coverage" / "executor-packet-20260907.json"
DEFAULT_AUDIT = ROOT / "docs" / "coverage" / "open-task-audit-20260907.json"

REQUIRED_GATES = {
    "runtime",
    "official_source",
    "degree_contract",
    "fixtures",
    "pagination_filters",
    "live_status",
    "quality_gate",
    "public_access",
}


def validate_packet(
    packet_path: Path = DEFAULT_PACKET, audit_path: Path = DEFAULT_AUDIT
) -> dict[str, Any]:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    live_audit = build_report(ROOT)
    packet_tasks = {
        (str(item["package"]), str(item["task_id"]))
        for item in packet.get("open_tasks", [])
        if isinstance(item, dict) and "package" in item and "task_id" in item
    }
    audit_tasks = {
        (str(item["package"]), str(item["task_id"]))
        for item in live_audit.get("tasks", [])
        if isinstance(item, dict) and "package" in item and "task_id" in item
    }
    persisted_tasks = {
        (str(item["package"]), str(item["task_id"]))
        for item in audit.get("tasks", [])
        if isinstance(item, dict) and "package" in item and "task_id" in item
    }
    if persisted_tasks != audit_tasks:
        raise ValueError("persisted open-task audit is stale; regenerate it first")
    excluded_packages = {
        str(package) for package in packet.get("scope_excludes", []) if isinstance(package, str)
    }
    scoped_audit_tasks = {task for task in audit_tasks if task[0] not in excluded_packages}
    if packet_tasks != scoped_audit_tasks:
        missing = sorted(scoped_audit_tasks - packet_tasks)
        stale = sorted(packet_tasks - scoped_audit_tasks)
        raise ValueError(f"executor packet task drift: missing={missing}, stale={stale}")
    if int(packet.get("verified_baseline", {}).get("state_appellate_complete", -1)) != 25:
        raise ValueError("packet baseline must be regenerated before changing the claimed state")
    if set(packet.get("promotion_gates", [])) != REQUIRED_GATES:
        raise ValueError("promotion gate set is incomplete or contains an unknown gate")
    forbidden = packet.get("forbidden_access_methods", [])
    if not isinstance(forbidden, list) or len(forbidden) < 8:
        raise ValueError("packet must preserve the forbidden access-method list")
    return {
        "status": "pass",
        "open_tasks": len(scoped_audit_tasks),
        "by_classification": {
            classification: sum(
                1
                for package, task_id in scoped_audit_tasks
                for item in live_audit.get("tasks", [])
                if item.get("package") == package
                and item.get("task_id") == task_id
                and item.get("classification") == classification
            )
            for classification in sorted(
                {
                    str(item.get("classification"))
                    for item in live_audit.get("tasks", [])
                    if item.get("package") not in excluded_packages
                }
            )
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    args = parser.parse_args()
    print(json.dumps(validate_packet(args.packet.resolve(), args.audit.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
