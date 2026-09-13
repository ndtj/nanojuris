from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from tools import run_trf5_live_smoke as smoke


def test_trf5_smoke_emits_standard_live_evidence(monkeypatch, tmp_path: Path) -> None:
    trace = SimpleNamespace(http_status=200, content_type="text/html")

    def make_page(page_number: int) -> SimpleNamespace:
        result = SimpleNamespace(
            id=f"trf5-{page_number}",
            number=f"000000{page_number}",
            summary="Resumo",
            raw={"id_documento": f"doc-{page_number}"},
        )
        return SimpleNamespace(
            source_trace=trace,
            page=page_number,
            page_size=1,
            results=[result],
            total=None,
            total_known=False,
        )

    document = SimpleNamespace(
        content_type="text/html",
        byte_size=64,
        sha256="b" * 64,
        text="Inteiro teor",
    )

    class FakeProvider:
        def __init__(self, *_args, **_kwargs):
            pass

        def search(self, query):
            return make_page(query.page)

        def get_document(self, _document_id):
            return document

    monkeypatch.setattr(smoke, "Trf5JurisprudenciaProvider", FakeProvider)
    output = tmp_path / "trf5.json"
    report = smoke.run(output)

    assert report["source_id"] == "trf5_jurisprudencia"
    assert report["classification"] == "valid"
    assert report["access_status"] == "public"
    assert report["content_sha256"] == "b" * 64
    assert report["full_text_status"] == "document_available"

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["limits"]["bodies_persisted"] is False
    assert "Inteiro teor" not in output.read_text(encoding="utf-8")
