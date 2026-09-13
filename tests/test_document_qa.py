from __future__ import annotations

from unittest.mock import patch

from tools.qa_jurisprudence_documents import _public_url_probe


class FakeResponse:
    def __init__(
        self,
        url: str,
        *,
        status_code: int,
        headers: dict[str, str],
        chunks: tuple[bytes, ...] = (),
    ) -> None:
        self.url = url
        self.status_code = status_code
        self.headers = headers
        self._chunks = chunks
        self.closed = False

    @property
    def is_redirect(self) -> bool:
        return 300 <= self.status_code < 400

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    def iter_content(self, *, chunk_size: int):
        del chunk_size
        return iter(self._chunks)

    def close(self) -> None:
        self.closed = True


def test_public_url_probe_rejects_off_host_redirect_before_following():
    response = FakeResponse(
        "https://court.example/document",
        status_code=302,
        headers={"location": "https://evil.example/payload"},
    )

    with patch("tools.qa_jurisprudence_documents.requests.get", return_value=response) as request:
        report = _public_url_probe("https://court.example/document", timeout=2)

    assert report["status"] == "redirect_outside_allowlist"
    assert request.call_count == 1
    assert response.closed is True


def test_public_url_probe_streams_allowlisted_redirect_and_hashes_document():
    redirect = FakeResponse(
        "https://court.example/document",
        status_code=302,
        headers={"location": "/document/1"},
    )
    final = FakeResponse(
        "https://court.example/document/1",
        status_code=200,
        headers={"content-type": "text/html; charset=utf-8"},
        chunks=(b"<html><body>texto</body></html>",),
    )

    with patch(
        "tools.qa_jurisprudence_documents.requests.get",
        side_effect=(redirect, final),
    ) as request:
        report = _public_url_probe("https://court.example/document", timeout=2)

    assert report["status"] == "reachable"
    assert report["redirects"][0]["location"] == "https://court.example/document/1"
    assert report["quality"]["status"] == "valid"
    assert report["response_bytes"] == len(b"<html><body>texto</body></html>")
    assert request.call_count == 2
    assert redirect.closed is True
    assert final.closed is True
