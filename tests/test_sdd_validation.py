from pathlib import Path

from tools.validate_sdd import _validate_compact_change, validate


def test_repository_sdd_packages_are_valid() -> None:
    root = Path(__file__).resolve().parents[1]

    assert validate(root) == []


def test_sdd_v2_rejects_acceptance_without_test(tmp_path) -> None:
    package = tmp_path / "0118-example"
    errors: list[str] = []
    _validate_compact_change(
        package,
        {
            "schema_version": "sdd-change-v2",
            "id": package.name,
            "status": "ready",
            "risk": "L2",
            "owner": "team:providers",
            "reviewer": "team:qa",
            "matrix_cells": ["surface:test"],
            "requirements": [{"id": "REQ-001", "acceptance": ["AC-001"]}],
            "tasks": [{"id": "T01", "requirements": ["REQ-001"]}],
            "tests": [{"id": "test-example", "acceptance": []}],
        },
        errors,
    )
    assert errors == [f"{package}: acceptance without test: AC-001"]
