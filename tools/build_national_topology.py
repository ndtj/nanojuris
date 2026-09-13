"""Build the versioned national topology artifact without network access."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = str(ROOT / "src")
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)

from nanojuris.catalog import load_provider_catalog  # noqa: E402
from nanojuris.topology import packaged_topology  # noqa: E402

DEFAULT_OUTPUT = ROOT / "docs" / "topology" / "national-topology.json"


def build(
    *, topology_version: str = "2026-09-01", cutoff_date: str | None = None
) -> dict[str, Any]:
    """Return the deterministic topology payload for a finite coverage epoch."""

    topology = packaged_topology(topology_version=topology_version)
    if cutoff_date is not None:
        # Rebuild through the court-level constructor so the requested cutoff is
        # represented explicitly without mutating the immutable topology object.
        from nanojuris.topology import topology_from_courts

        topology = topology_from_courts(
            topology_version=topology_version,
            cutoff_date=cutoff_date,
            provider_ids=(
                str(entry.get("source_id", ""))
                for entry in load_provider_catalog().get("entries", [])
                if entry.get("source_id")
            ),
        )
    return topology.to_dict()


def write(output: Path, payload: dict[str, Any]) -> None:
    """Write a stable, human-readable JSON artifact."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--topology-version", default="2026-09-01")
    parser.add_argument("--cutoff-date")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    payload = build(topology_version=args.topology_version, cutoff_date=args.cutoff_date)
    write(output, payload)
    print(
        json.dumps(
            {
                "output": str(output),
                "collections": len(payload["collections"]),
                "epochs": len(payload["epochs"]),
                "network_access": payload["metadata"]["network_access"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
