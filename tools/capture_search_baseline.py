"""Capture an immutable pre-change reference from the current git HEAD."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "benchmarks" / "live-ranking-baseline-20260907.json"
REFERENCE_FILES = (
    "src/nanojuris/client.py",
    "tests/test_client_exporters.py",
    "tests/test_routing.py",
    "tests/test_provider_contract_v2.py",
    "docs/benchmarks/live-ranking-v1.json",
)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _head_bytes(path: str) -> bytes | None:
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"HEAD:{path}"], cwd=ROOT, capture_output=True
    )
    if exists.returncode != 0:
        return None
    try:
        return subprocess.check_output(
            ["git", "show", f"HEAD:{path}"], cwd=ROOT, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return None


def capture(output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    commit = _git("rev-parse", "HEAD")
    references: list[dict[str, Any]] = []
    for path in REFERENCE_FILES:
        data = _head_bytes(path)
        if data is not None:
            references.append(
                {"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            )
    fixtures: list[dict[str, Any]] = []
    for path in _git("ls-tree", "-r", "--name-only", "HEAD", "tests/fixtures").splitlines():
        data = _head_bytes(path)
        if data is not None:
            fixtures.append(
                {"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            )
    report = {
        "schema_version": "live-ranking-baseline-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reference_commit": commit,
        "capture_mode": "immutable_head_reconstruction",
        "pre_code_snapshot_available": True,
        "raw_payloads_persisted": False,
        "reference_files": references,
        "offline_fixture_manifest": fixtures,
        "commands": [
            "python -m pytest -q tests/test_client_exporters.py tests/test_routing.py "
            "tests/test_provider_contract_v2.py",
            "python -m ruff check .",
            "python -m mypy src",
        ],
        "notes": (
            "The worktree already contained implementation edits when this SDD was resumed. "
            "The immutable HEAD commit is used as the pre-change baseline; only hashes and "
            "metadata are persisted."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = capture(args.output.resolve())
    print(
        json.dumps(
            {
                "commit": report["reference_commit"],
                "fixtures": len(report["offline_fixture_manifest"]),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
