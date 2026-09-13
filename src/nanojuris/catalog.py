"""Read the provider capability catalog shipped with NanoJuris.

The repository keeps the full evidence-rich registry under ``docs/`` and, for
source-checkout compatibility, may also expose its generated copy under
``src``. Published artifacts ship only the compact runtime projection so the
library remains small without losing the provider identity/capability contract.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any


@lru_cache(maxsize=1)
def load_provider_catalog() -> dict[str, Any]:
    """Return the packaged machine-readable catalog, or an empty catalog in development."""

    try:
        package_data = resources.files("nanojuris").joinpath("data")
        # Prefer the full registry in a development checkout so audit tooling
        # retains its evidence-rich behavior.  Wheels/sdists include only the
        # compact projection below.
        for filename in ("provider-catalog.full.json", "provider-catalog.json"):
            try:
                raw = package_data.joinpath(filename).read_text(encoding="utf-8")
                break
            except FileNotFoundError:
                continue
        else:
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
