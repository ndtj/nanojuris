from __future__ import annotations

from nanojuris import FetchedContent, ParsedContent
from nanojuris import FetchRequest as PublicFetchRequest
from nanojuris import HttpFetcher as PublicHttpFetcher
from nanojuris.config import NanoJurisConfig
from nanojuris.extraction import FetchRequest, HttpFetcher, parsed_content
from nanojuris.models import AccessStatus, ExtractionStatus


class FakeResponse:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code
        self.headers = {"Content-Type": "text/html; charset=utf-8"}
        self.encoding = "utf-8"


class FakeSession:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls = []
        self.trust_env = True
        self.verify = True

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.response


def test_http_fetcher_returns_traced_raw_content():
    session = FakeSession(FakeResponse(b"<html>ok</html>"))
    fetcher = HttpFetcher(
        NanoJurisConfig(
            timeout=3.0,
            user_agent="NanoJuris Test",
            trust_env=False,
            verify_ssl=False,
        ),
        session,
    )

    content = fetcher.fetch(
        FetchRequest(
            source="fake",
            url="https://example.test/resultados",
            endpoint="/resultados",
            method="POST",
            data={"q": "icms"},
            query={"text": "icms"},
            limitations=["fixture offline"],
        )
    )

    assert content.text == "<html>ok</html>"
    assert content.byte_size == 15
    assert content.access_status == AccessStatus.PUBLIC
    assert content.source_trace is not None
    assert content.source_trace.provider == "fake"
    assert session.calls[0]["method"] == "POST"
    assert session.calls[0]["kwargs"]["headers"]["User-Agent"] == "NanoJuris Test"
    assert session.calls[0]["kwargs"]["timeout"] == 3.0
    assert session.calls[0]["kwargs"]["verify"] is False
    assert session.trust_env is False
    assert session.verify is False


def test_extraction_primitives_are_public_api():
    assert PublicFetchRequest is FetchRequest
    assert PublicHttpFetcher is HttpFetcher
    assert FetchedContent.__name__ == "FetchedContent"
    assert ParsedContent.__name__ == "ParsedContent"


def test_http_fetcher_maps_access_status_from_status_code():
    session = FakeSession(FakeResponse(b"blocked", status_code=403))
    fetcher = HttpFetcher(session=session)

    content = fetcher.fetch(
        FetchRequest(source="fake", url="https://example.test/restrito", endpoint="/restrito")
    )

    assert content.access_status == AccessStatus.ACCESS_CONTROL_REQUIRED


def test_parsed_content_includes_extraction_trace():
    parsed = parsed_content(
        source="fake",
        parser="fake.parser",
        parser_version="1",
        records=[{"id": "r1"}],
        status=ExtractionStatus.PARTIAL,
        access_status=AccessStatus.PARTIAL,
        content_sha256="abc",
        content_bytes=10,
        warnings=["campo opcional ausente"],
    )

    assert parsed.records == [{"id": "r1"}]
    assert parsed.extraction_trace is not None
    assert parsed.extraction_trace.status == ExtractionStatus.PARTIAL
    assert parsed.extraction_trace.access_status == AccessStatus.PARTIAL
    assert parsed.extraction_trace.content_sha256 == "abc"
