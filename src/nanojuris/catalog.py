"""Read the generated provider catalog shipped with the NanoJuris package."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any


@lru_cache(maxsize=1)
def load_provider_catalog() -> dict[str, Any]:
    """Return the packaged machine-readable catalog, or an empty catalog in development."""

    try:
        raw = (
            resources.files("nanojuris")
            .joinpath("data/provider-catalog.full.json")
            .read_text(encoding="utf-8")
        )
    except (FileNotFoundError, ModuleNotFoundError):
        return {"entries": []}
    return json.loads(raw)


def get_provider_catalog_entry(source_id: str) -> dict[str, Any] | None:
    """Return one source entry from the packaged catalog."""

    for entry in load_provider_catalog().get("entries", []):
        if entry.get("source_id") == source_id:
            return entry
    return None
