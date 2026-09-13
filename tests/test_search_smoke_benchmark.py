from __future__ import annotations

import json
from pathlib import Path

from tools import run_search_smoke_benchmark as smoke


def test_smoke_summary_never_serializes_result_bodies(tmp_path: Path, monkeypatch) -> None:
    class FakeClient:
        def __init__(self, *, config) -> None:
            self.config = config

        def search_many(self, query: str, **kwargs):
            assert kwargs["mode"] == "selected"
            return {
                "searched_sources": ["fixture"],
                "source_outcomes_v2": {
                    "fixture": {
                        "status": "success_with_results",
                        "candidate_count": 1,
                        "latency_ms": 1.0,
                    }
                },
                "source_completeness": {"fixture": {"returned": 1}},
                "errors": [],
                "total_returned": 1,
                "ranking_complete": True,
                "collection_complete": True,
                "results": [{"summary": "must not be persisted"}],
            }

    monkeypatch.setattr(smoke, "NanoJurisClient", FakeClient)
    output = tmp_path / "smoke.json"
    report = smoke.run(source="fixture", output=output)
    assert report["queries"] == 6
    assert "must not be persisted" not in output.read_text(encoding="utf-8")
    assert json.loads(output.read_text(encoding="utf-8"))["limits"]["bodies_persisted"] is False
