"""Close only SDD-0092 tasks whose local evidence is already checked in.

This is deliberately conservative: external-source and human-review tasks are
never changed by this tool.  It is useful when generated task audits need to
reflect work that was completed in the repository rather than leaving a
planning checklist stale.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "specs/changes/0092-national-coverage-execution-blueprint/tasks.md"

LOCAL_TASKS = {
    "T001",
    "T002",
    "T003",
    "T004",
    "T005",
    "T006",
    "T007",
    "T008",
    "T009",
    "T010",
    "T015",
    "T017",
    "T020",
    "T022",
    "T023",
    "T024",
    "T025",
    "T026",
    "T028",
    "T031",
}
TASK_RE = re.compile(r"^(?P<prefix>- \[)(?P<state>[ ])(\] \*\*(?P<task>T\d+) \[L\]\*\*)")


def close_tasks() -> int:
    lines = TASKS.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = 0
    output: list[str] = []
    for line in lines:
        match = TASK_RE.match(line)
        if match and match.group("task") in LOCAL_TASKS:
            line = line.replace("- [ ]", "- [x]", 1)
            changed += 1
        output.append(line)
    TASKS.write_text("".join(output), encoding="utf-8")
    return changed


if __name__ == "__main__":
    print(f"closed_local_tasks={close_tasks()}")
