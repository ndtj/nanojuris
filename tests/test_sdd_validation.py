from pathlib import Path

from tools.validate_sdd import validate


def test_repository_sdd_packages_are_valid() -> None:
    root = Path(__file__).resolve().parents[1]

    assert validate(root) == []
