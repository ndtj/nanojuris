from __future__ import annotations

import json

from tools.build_0091_baseline import OUTPUT, build


def test_0091_baseline_is_hash_bound_and_reproducible() -> None:
    payload = build()
    stored = json.loads(OUTPUT.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "1.2"
    assert payload["artifact_sha256"]
    assert payload["values"]["runtime_providers"] == 80
    assert payload == stored
