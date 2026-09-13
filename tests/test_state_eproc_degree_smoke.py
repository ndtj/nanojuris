from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from nanojuris.models import JurisprudenceQuery
from tools import run_state_eproc_degree_smoke as smoke


def test_probe_writes_only_redacted_degree_evidence(tmp_path: Path, monkeypatch) -> None:
    class FakeProvider:
        def __init__(self, _config):
            pass

        def search(self, _query: JurisprudenceQuery):
            trace = SimpleNamespace(
                endpoint="POST /search",
                http_status=200,
                final_url="https://example.test/search",
                response_bytes=42,
                content_sha256="a" * 64,
            )
            result = SimpleNamespace(
                id="fixture-second-1", court="TJ", source="fake", degree="second"
            )
            return SimpleNamespace(results=[result], total=1, total_known=True, source_trace=trace)

    monkeypatch.setattr(smoke, "PROVIDERS", {"fake": FakeProvider})
    output = tmp_path / "degree.json"
    payload = smoke.run(output)

    assert payload["summary"]["search_valid"] == 1
    assert payload["results"][0]["degrees"] == ["second"]
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    assert "response_body" not in serialized
    assert output.exists()
