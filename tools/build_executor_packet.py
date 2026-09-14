"""Generate the compact executor packet from the active SDD task audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_open_tasks import build_report  # noqa: E402

OUTPUT = ROOT / "docs" / "coverage" / "executor-packet-20260907.json"


def build(root: Path = ROOT, existing_path: Path = OUTPUT) -> dict[str, Any]:
    """Keep policy metadata while deriving the active task list deterministically."""

    existing: dict[str, Any] = {}
    if existing_path.is_file():
        existing = json.loads(existing_path.read_text(encoding="utf-8"))
    audit = build_report(root)
    excluded = set(existing.get("scope_excludes", []))
    tasks = [
        {
            "package": item["package"],
            "task_id": item["task_id"],
            "class": item["classification"],
            "scope": item["next_action"],
        }
        for item in audit["tasks"]
        if item["package"] not in excluded
    ]
    packet = dict(existing)
    packet["schema_version"] = "nanojuris-executor-packet-v1"
    packet["generated_at"] = "2026-09-14"
    packet["open_tasks"] = tasks
    return packet


def write(path: Path = OUTPUT) -> dict[str, Any]:
    payload = build(existing_path=path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = write()
    print(json.dumps({"open_tasks": len(result["open_tasks"])}, sort_keys=True))
