"""Read the provider capability catalog shipped with NanoJuris.

The repository keeps the evidence-rich registry under ``docs/``. Published
artifacts and runtime load only the compact projection, keeping the core wheel
small without losing provider identity and capability contracts.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def load_provider_catalog() -> dict[str, Any]:
    """Return the packaged machine-readable catalog, or an empty catalog in development."""

    # Development tools need the evidence-rich catalog, but it must not be
    # duplicated inside ``src`` or shipped in the wheel.  This path only exists
    # in a source checkout; an installed package always falls back to compact
    # package data below.
    source_catalog = (
        Path(__file__).resolve().parents[2] / "docs" / "registry" / "provider-catalog.full.json"
    )
    if source_catalog.is_file():
        return json.loads(source_catalog.read_text(encoding="utf-8"))
    try:
        package_data = resources.files("nanojuris").joinpath("data")
        try:
            raw = package_data.joinpath("provider-catalog.json").read_text(encoding="utf-8")
        except FileNotFoundError:
            return {"entries": []}
    except ModuleNotFoundError:
        return {"entries": []}
    return json.loads(raw)


def get_provider_catalog_entry(source_id: str) -> dict[str, Any] | None:
    """Return one source entry from the packaged catalog."""

    for entry in load_provider_catalog().get("entries", []):
        if entry.get("source_id") == source_id:
            return entry
    return None
