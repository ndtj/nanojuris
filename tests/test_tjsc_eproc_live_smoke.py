from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from tools import run_tjsc_eproc_live_smoke as smoke


def test_tjsc_live_smoke_writes_redacted_success_envelope(monkeypatch, tmp_path: Path) -> None:
    trace = SimpleNamespace(http_status=200, content_type="text/html")

    def make_page(page_number: int) -> SimpleNamespace:
        result = SimpleNamespace(
            id=f"tjsc-eproc-jurisprudencia-{4870937 + page_number}",
            number=None,
            summary="Resumo",
        )
        return SimpleNamespace(
            source_trace=trace,
            page=page_number,
            page_size=2,
            results=[result],
            total=2,
            total_known=True,
            access_status=SimpleNamespace(value="public"),
            extraction_status=SimpleNamespace(value="complete"),
        )

    document = SimpleNamespace(
        source_trace=trace,
        content_type="text/html",
        byte_size=32,
        sha256="a" * 64,
        text="Inteiro teor",
        extraction_trace=SimpleNamespace(status=SimpleNamespace(value="complete")),
    )

    class FakeProvider:
        def __init__(self, *_args, **_kwargs):
            pass

        def search(self, query):
            return make_page(query.page)

        def get_document(self, _document_id):
            return document

    monkeypatch.setattr(smoke, "TjscEprocJurisprudenciaProvider", FakeProvider)
    output = tmp_path / "tjsc.json"
    report = smoke.run(output)

    assert report["summary"] == {
        "search_valid": True,
        "pagination_valid": True,
        "detail_valid": True,
        "errors": 0,
    }
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["limits"]["bodies_persisted"] is False
    assert "Inteiro teor" not in output.read_text(encoding="utf-8")
