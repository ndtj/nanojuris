"""Validate the minimum topology and traceability of SDD change packages."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_FILES = ("spec.md", "design.md", "tasks.md", "verification.md")
VALID_STATUSES = {"proposed", "in_progress", "verified", "accepted", "superseded"}
PACKAGE_ID = re.compile(r"^\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*$")
STATUS = re.compile(r"^Status:\s*`?([a-z_]+)`?", re.MULTILINE)
CRITERION = re.compile(r"\bAC-\d{3}\b")
TASK = re.compile(r"\bT\d{1,3}\b")


def validate(root: Path) -> list[str]:
    """Return validation errors for all change packages below ``root``."""
    changes = root / "specs" / "changes"
    if not changes.is_dir():
        return [f"missing SDD changes directory: {changes}"]

    errors: list[str] = []
    packages = sorted(path for path in changes.iterdir() if path.is_dir())
    if not packages:
        return [f"no SDD change packages found in: {changes}"]

    for package in packages:
        if not PACKAGE_ID.fullmatch(package.name):
            errors.append(f"{package}: package id must match NNNN-lowercase-name")
        contents: dict[str, str] = {}
        for filename in REQUIRED_FILES:
            path = package / filename
            if not path.is_file():
                errors.append(f"{package}: missing {filename}")
                continue
            contents[filename] = path.read_text(encoding="utf-8")

        spec = contents.get("spec.md", "")
        status = STATUS.search(spec)
        if not status:
            errors.append(f"{package}: spec.md is missing Status")
        elif status.group(1) not in VALID_STATUSES:
            errors.append(f"{package}: invalid status {status.group(1)!r}")
        if not CRITERION.search(spec):
            errors.append(f"{package}: spec.md needs at least one AC-NNN criterion")

        tasks = contents.get("tasks.md", "")
        if not TASK.search(tasks):
            errors.append(f"{package}: tasks.md needs at least one TNN task")

        verification = contents.get("verification.md", "")
        if "## Resultados" not in verification and "## Comandos e resultados" not in verification:
            errors.append(f"{package}: verification.md needs a results section")
        if "## Rastreabilidade" not in verification:
            errors.append(f"{package}: verification.md needs a Rastreabilidade section")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("SDD validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
