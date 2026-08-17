"""Enforce conservative size budgets for distributable NanoJuris artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

STATIC_BUDGET = 300_000
WHEEL_BUDGET = 600_000
SDIST_BUDGET = 1_500_000


def directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--static-dir",
        type=Path,
        default=Path("src/nanojuris/web/static"),
    )
    parser.add_argument("--distribution", type=Path, default=None)
    args = parser.parse_args()

    static_size = directory_size(args.static_dir)
    print(f"static assets: {static_size:,} bytes / {STATIC_BUDGET:,}")
    failures: list[str] = []
    if static_size > STATIC_BUDGET:
        failures.append("static assets excedem o orcamento")

    if args.distribution is not None:
        artifacts = sorted(args.distribution.glob("*.whl"))
        if not artifacts:
            failures.append("nenhum wheel encontrado")
        for artifact in artifacts:
            size = artifact.stat().st_size
            print(f"wheel {artifact.name}: {size:,} bytes / {WHEEL_BUDGET:,}")
            if size > WHEEL_BUDGET:
                failures.append(f"{artifact.name} excede o orcamento")
        sdists = sorted(args.distribution.glob("*.tar.gz"))
        for artifact in sdists:
            size = artifact.stat().st_size
            print(f"sdist {artifact.name}: {size:,} bytes / {SDIST_BUDGET:,}")
            if size > SDIST_BUDGET:
                failures.append(f"{artifact.name} excede o orcamento")

    if failures:
        for failure in failures:
            print(f"ERRO: {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
