"""Classify unchecked SDD tasks for the next safe execution cycle."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "docs" / "coverage" / "open-task-audit-20260907.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "coverage" / "open-task-audit-20260907.md"
TASK_LINE = re.compile(r"^-\s+\[\s\]\s+(?:\*\*)?(T\d+[A-Z]?)(?:\*\*)?\s*[—-]?\s*(.*)$")

EXTERNAL_IDS = {
    ("0069-state-appellate-national-coverage", "T07"),
    ("0078-national-coverage-lawful-access", "T012"),
    ("0078-national-coverage-lawful-access", "T013"),
    ("0078-national-coverage-lawful-access", "T014"),
    ("0078-national-coverage-lawful-access", "T015"),
    ("0078-national-coverage-lawful-access", "T016"),
    ("0078-national-coverage-lawful-access", "T017"),
    ("0078-national-coverage-lawful-access", "T019"),
    ("0078-national-coverage-lawful-access", "T021"),
    ("0078-national-coverage-lawful-access", "T022"),
    ("0078-national-coverage-lawful-access", "T024"),
    ("0078-national-coverage-lawful-access", "T025"),
    ("0081-state-first-degree-expansion", "T003"),
    ("0081-state-first-degree-expansion", "T004"),
    ("0081-state-first-degree-expansion", "T005"),
    ("0081-state-first-degree-expansion", "T006"),
    ("0082-national-labor-electoral-families", "T001"),
    ("0082-national-labor-electoral-families", "T002"),
    ("0082-national-labor-electoral-families", "T003"),
    ("0082-national-labor-electoral-families", "T004"),
    ("0082-national-labor-electoral-families", "T005"),
    ("0082-national-labor-electoral-families", "T006"),
    ("0083-federal-superior-military-closure", "T001"),
    ("0083-federal-superior-military-closure", "T002"),
    ("0083-federal-superior-military-closure", "T003"),
    ("0083-federal-superior-military-closure", "T004"),
    ("0083-federal-superior-military-closure", "T005"),
    ("0084-fulltext-and-field-completeness", "T002"),
    ("0084-fulltext-and-field-completeness", "T004"),
    ("0084-fulltext-and-field-completeness", "T005"),
    ("0087-trf3-jurisprudencia-exact-process", "T008"),
    ("0089-national-coverage-execution-handoff", "T007"),
    ("0089-national-coverage-execution-handoff", "T008"),
    ("0089-national-coverage-execution-handoff", "T009"),
    ("0089-national-coverage-execution-handoff", "T010"),
    ("0089-national-coverage-execution-handoff", "T011"),
    ("0089-national-coverage-execution-handoff", "T013"),
    ("0089-national-coverage-execution-handoff", "T014"),
    ("0089-national-coverage-execution-handoff", "T015"),
    ("0089-national-coverage-execution-handoff", "T016"),
    ("0089-national-coverage-execution-handoff", "T017"),
    ("0089-national-coverage-execution-handoff", "T018"),
    ("0089-national-coverage-execution-handoff", "T019"),
    ("0089-national-coverage-execution-handoff", "T020"),
    ("0089-national-coverage-execution-handoff", "T021"),
    ("0089-national-coverage-execution-handoff", "T025"),
    ("0089-national-coverage-execution-handoff", "T026"),
    ("0094-trt8-pje-jurisprudencia", "T009"),
}
HUMAN_IDS = {
    ("0077-live-intelligent-federated-search", "T62"),
    ("0086-trt2-basis-jurisprudencia", "T009"),
    ("0089-national-coverage-execution-handoff", "T036"),
    ("0089-national-coverage-execution-handoff", "T037"),
    ("0090-tjrj-banco-sentencas", "T008"),
}


def _classification(package: str, task_id: str, marker: str | None = None) -> tuple[str, str, str]:
    key = (package, task_id)
    if key in HUMAN_IDS:
        return (
            "human_review",
            "Add independent relevance labels, calibrate on development, and evaluate holdout.",
            "Code must not fabricate legal relevance judgments.",
        )
    if key in EXTERNAL_IDS:
        return (
            "external_source",
            "Run a bounded official-source check or record the terminal external blocker.",
            "Adapters and catalog declarations are not evidence of a live route.",
        )
    if marker in {"H", "E/H", "H/E"}:
        return (
            "human_review",
            "Record the responsible human decision before closing the task.",
            "An agent must not fabricate legal, retention, relevance or promotion approval.",
        )
    if marker in {"E", "E/H", "H/E"}:
        return (
            "external_source",
            "Run a bounded official-source check or record the terminal external blocker.",
            "The task depends on a source, route or external action not reproducible locally.",
        )
    return (
        "local_evidence",
        "Create the missing local artifact/test and rerun the relevant gates.",
        "This task is not classified as externally blocked by the current map.",
    )


def build_report(root: Path = ROOT) -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    for path in sorted((root / "specs" / "changes").glob("*/tasks.md")):
        package = path.parent.name
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = TASK_LINE.match(line.strip())
            if not match:
                continue
            task_id, description = match.groups()
            # Combined markers such as [E/H] depend on an external source and
            # a human decision; they must not silently become local work.
            marker_match = re.search(r"\[([LEH](?:/[EH])?)\]", line)
            marker = marker_match.group(1) if marker_match else None
            classification, next_action, rationale = _classification(package, task_id, marker)
            tasks.append(
                {
                    "package": package,
                    "task_id": task_id,
                    "description": description.strip(),
                    "classification": classification,
                    "next_action": next_action,
                    "rationale": rationale,
                    "path": str(path.relative_to(root)).replace("\\", "/"),
                    "line": line_number,
                }
            )
    counts: dict[str, int] = {}
    for task in tasks:
        kind = str(task["classification"])
        counts[kind] = counts.get(kind, 0) + 1
    return {
        "schema_version": "open-task-audit-v1",
        "generated_at": "2026-09-07",
        "open_tasks": len(tasks),
        "by_classification": counts,
        "tasks": tasks,
    }


def write_report(
    root: Path = ROOT,
    *,
    output: Path = DEFAULT_JSON,
    markdown: Path = DEFAULT_MARKDOWN,
) -> dict[str, Any]:
    report = build_report(root)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Open task audit - 2026-09-07",
        "",
        f"Unchecked tasks: **{report['open_tasks']}**.",
        "",
        "| Package | Task | Classification | Next action |",
        "|---|---|---|---|",
    ]
    for task in report["tasks"]:
        lines.append(
            f"| `{task['package']}` | `{task['task_id']}` | `{task['classification']}` | "
            f"{task['next_action']} |"
        )
    markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    report = write_report(
        args.root.resolve(), output=args.output.resolve(), markdown=args.markdown.resolve()
    )
    print(
        json.dumps(
            {"open_tasks": report["open_tasks"], "by_classification": report["by_classification"]}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
