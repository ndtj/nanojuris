from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from nanojuris.models import JurisprudenceQuery
from tools import run_cjsg_live_smoke as smoke


class _Provider:
    def __init__(self, *, detail: str = "valid") -> None:
        self.detail = detail

    def search(self, query: JurisprudenceQuery):  # noqa: ARG002 - protocol double
        trace = SimpleNamespace(
            endpoint="/trocaDePagina.do",
            http_status=200,
            content_type="text/html",
            response_bytes=123,
            content_sha256="search-hash",
            retrieval_status="ok",
            final_url="https://example.test/result",
        )
        result = SimpleNamespace(id="tj-cjsg-1-0", summary="ementa", court="TJ", source="fake")
        return SimpleNamespace(results=[result], total=12, total_known=True, source_trace=trace)

    def get_document(self, result_id: str):  # noqa: ARG002 - protocol double
        if self.detail == "access_control_required":
            from nanojuris.errors import AccessControlRequiredError

            raise AccessControlRequiredError("captcha")
        trace = SimpleNamespace(
            http_status=200,
            content_type="application/pdf",
            response_bytes=20,
            content_sha256="detail-hash",
        )
        return SimpleNamespace(
            byte_size=20,
            content_type="application/pdf",
            sha256="detail-hash",
            extraction_status="partial",
            text="",
            source_trace=trace,
        )


def test_probe_preserves_detail_access_control_state() -> None:
    report = smoke._probe(
        "fake",
        lambda config: _Provider(detail="access_control_required"),
        JurisprudenceQuery(text="responsabilidade civil", page_size=2),
    )

    assert report["classification"] == "reachable_valid_data"
    assert report["record_count_observed"] == 1
    assert report["observation"]["detail"]["status"] == "access_control_required"
    assert "raw_body" not in json.dumps(report).lower()


def test_probe_classifies_search_access_control_separately() -> None:
    from nanojuris.errors import AccessControlRequiredError

    class BlockedProvider:
        def __init__(self, config):  # noqa: ARG002 - protocol double
            pass

        def search(self, query: JurisprudenceQuery):  # noqa: ARG002 - protocol double
            raise AccessControlRequiredError("captcha token required")

    report = smoke._probe(
        "blocked",
        BlockedProvider,
        JurisprudenceQuery(text="responsabilidade civil", page_size=2),
    )

    assert report["classification"] == "access_blocked"
    assert report["observation"]["error"]["type"] == "AccessControlRequiredError"


def test_run_writes_bounded_redacted_envelope(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(smoke, "PROVIDERS", {"fake": lambda config: _Provider()})
    output = tmp_path / "cjsg.json"

    payload = smoke.run(output, text="responsabilidade civil", page_size=2)

    assert payload["summary"] == {
        "sources": 1,
        "search_valid": 1,
        "search_empty": 0,
        "search_errors": 0,
        "search_blocked": 0,
        "search_rate_limited": 0,
        "search_schema_invalid": 0,
        "detail_access_controlled": 0,
        "detail_valid": 1,
    }
    assert output.exists()
    assert "cookie" not in output.read_text(encoding="utf-8").lower()
