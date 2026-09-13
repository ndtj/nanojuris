from __future__ import annotations

import json
from pathlib import Path

from tools import run_tjro_liame_live_smoke as smoke


def test_live_smoke_redacts_body_and_reports_summary(tmp_path: Path, monkeypatch) -> None:
    class FakePage:
        source_trace = type(
            "Trace",
            (),
            {"http_status": 200, "content_type": "application/json", "response_bytes": 100},
        )()
        page = 1
        page_size = 2
        total = 1
        total_known = True
        results = [
            type(
                "Result",
                (),
                {"id": "liame-1", "question": "q", "thesis": "t"},
            )()
        ]
        access_status = "public"
        extraction_status = "complete"

    class FakeProvider:
        def __init__(self, config) -> None:
            self.calls = 0

        def search(self, query):
            self.calls += 1
            page = FakePage()
            page.page = self.calls
            return page

    monkeypatch.setattr(smoke, "TjroLiameProvider", FakeProvider)
    output = tmp_path / "smoke.json"
    report = smoke.run(output)

    assert report["summary"]["search_valid"] is True
    assert report["summary"]["pagination_valid"] is False
    assert report["summary"]["total_known"] is True
    serialized = json.loads(output.read_text(encoding="utf-8"))
    assert "body" not in serialized
