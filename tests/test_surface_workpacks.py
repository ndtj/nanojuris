from __future__ import annotations

import json

from tools.build_surface_workpacks import MANIFEST, build


def test_every_canonical_surface_has_a_materialized_workpack() -> None:
    payload = build()
    stored = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert payload == stored
    assert payload["surface_count"] == 151
    assert payload["required_surface_count"] == 125
    assert len(payload["workpacks"]) == payload["surface_count"]
    assert all(item["relative_path"].endswith(".md") for item in payload["workpacks"])
    assert all(len(item["gates"]) == 8 for item in payload["workpacks"])
