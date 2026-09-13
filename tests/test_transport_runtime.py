from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.documents import (
    ContentAddressedDocumentCache,
    DocumentReference,
    fetch_document_reference,
)
from nanojuris.errors import ParserContractChangedError
from nanojuris.transport import (
    ContentResponseCache,
    SharedHttpClient,
    TransportPolicy,
    TransportRequest,
    TransportStatus,
)


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        body: bytes = b"ok",
        *,
        headers: dict[str, str] | None = None,
        url: str = "https://example.test/api",
        redirect: bool = False,
    ) -> None:
        self.status_code = status_code
        self.content = body
        self.headers = headers or {"Content-Type": "application/json"}
        self.url = url
        self.is_redirect = redirect
        self.closed = False

    def iter_content(self, chunk_size: int = 1):
        for index in range(0, len(self.content), max(1, chunk_size)):
            yield self.content[index : index + max(1, chunk_size)]

    def close(self) -> None:
        self.closed = True


class FakeSession:
    def __init__(self, responses: list[FakeResponse | Exception]) -> None:
        self.responses = iter(responses)
        self.headers: dict[str, str] = {}
        self.trust_env = True
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def request_for(
    *, url: str = "https://example.test/api", method: str = "GET", **kwargs
) -> TransportRequest:
    return TransportRequest(
        source="test",
        operation="search",
        method=method,
        url=url,
        **kwargs,
    )


def test_transport_rejects_non_allowlisted_and_http_urls() -> None:
    client = SharedHttpClient(
        TransportPolicy(allowed_hosts=("example.test",)), session=FakeSession([])
    )
    with pytest.raises(ValueError):
        client.request(request_for(url="https://other.test/api"))
    with pytest.raises(ValueError):
        client.request(request_for(url="http://example.test/api"))


def test_transport_retries_idempotent_and_honors_retry_after() -> None:
    session = FakeSession(
        [
            FakeResponse(503, headers={"Retry-After": "0.01"}),
            FakeResponse(200, body=b"{}"),
        ]
    )
    delays: list[float] = []
    client = SharedHttpClient(
        TransportPolicy(allowed_hosts=("example.test",), rate_limit_interval=0),
        session=session,
        sleep_fn=delays.append,
    )
    response = client.request(request_for())
    assert response.status_code == 200
    assert response.status is TransportStatus.COMPLETE
    assert len(session.calls) == 2
    assert delays == [0.01]


def test_transport_never_retries_non_idempotent() -> None:
    session = FakeSession([FakeResponse(503), FakeResponse(200)])
    client = SharedHttpClient(
        TransportPolicy(allowed_hosts=("example.test",), rate_limit_interval=0), session=session
    )
    response = client.request(request_for(method="POST", idempotent=False))
    assert response.status_code == 503
    assert len(session.calls) == 1


def test_transport_classifies_oversize_and_preserves_hash() -> None:
    session = FakeSession([FakeResponse(200, body=b"12345")])
    client = SharedHttpClient(
        TransportPolicy(allowed_hosts=("example.test",), max_bytes=4, rate_limit_interval=0),
        session=session,
    )
    response = client.request(request_for())
    assert response.status is TransportStatus.RESPONSE_TOO_LARGE
    assert response.body == b"1234"
    assert response.content_sha256


def test_transport_follows_only_allowlisted_redirects() -> None:
    session = FakeSession(
        [
            FakeResponse(
                302,
                body=b"",
                headers={"Location": "https://example.test/redirected"},
                url="https://example.test/api",
                redirect=True,
            ),
            FakeResponse(200, body=b"{}", url="https://example.test/redirected"),
        ]
    )
    client = SharedHttpClient(
        TransportPolicy(allowed_hosts=("example.test",), rate_limit_interval=0), session=session
    )
    response = client.request(request_for())
    assert response.status is TransportStatus.COMPLETE
    assert response.final_url == "https://example.test/redirected"
    assert len(response.redirects) == 1


def test_transport_cache_roundtrip(tmp_path: Path) -> None:
    cache = ContentResponseCache(tmp_path / "responses")
    response = FakeResponse(200, body=b"cached")
    from nanojuris.transport.models import TransportResponse

    envelope = TransportResponse(
        status_code=response.status_code,
        url=response.url,
        final_url=response.url,
        headers=response.headers,
        body=response.content,
        elapsed_ms=1.0,
    )
    cache.put("a" * 64, envelope)
    restored = cache.get("a" * 64)
    assert restored is not None
    assert restored.body == b"cached"


def test_transport_cache_key_is_namespaced_by_contract_version() -> None:
    first = request_for(cacheable=True, cache_version="live-response-v1")
    second = request_for(cacheable=True, cache_version="live-response-v2")
    assert first.cache_key() != second.cache_key()


def test_transport_cache_version_is_bounded() -> None:
    with pytest.raises(ValueError, match="cache_version"):
        request_for(cache_version=" ")
    with pytest.raises(ValueError, match="cache_version"):
        request_for(cache_version="x" * 65)


def test_transport_cache_ttl_uses_explicit_zero_timestamp(tmp_path: Path) -> None:
    cache = ContentResponseCache(tmp_path / "responses", ttl_seconds=10)
    from nanojuris.transport.models import TransportResponse

    envelope = TransportResponse(
        status_code=200,
        url="https://example.test/api",
        final_url="https://example.test/api",
        headers={"Content-Type": "application/json"},
        body=b"cached",
        elapsed_ms=1.0,
    )
    key = "b" * 64
    cache.put(key, envelope)
    path = cache._path(key)
    import os

    os.utime(path, (0, 0))
    assert cache.get(key, now=0) is not None
    assert cache.get(key, now=11) is None


def test_transport_cache_supports_bounded_stale_reads(tmp_path: Path) -> None:
    cache = ContentResponseCache(tmp_path / "responses", ttl_seconds=10)
    from nanojuris.transport.models import TransportResponse

    envelope = TransportResponse(
        status_code=200,
        url="https://example.test/api",
        final_url="https://example.test/api",
        headers={"ETag": '"v1"'},
        body=b"cached",
        elapsed_ms=1.0,
    )
    key = "f" * 64
    cache.put(key, envelope)
    import os

    path = cache._path(key)
    os.utime(path, (100, 100))
    assert cache.get(key, now=111) is None
    stale = cache.get_stale(key, max_age_seconds=20, now=111)
    assert stale is not None
    assert stale.body == b"cached"
    assert cache.get_stale(key, max_age_seconds=5, now=111) is None


def test_transport_revalidates_with_etag_and_reuses_body(tmp_path: Path) -> None:
    cache = ContentResponseCache(tmp_path / "responses", ttl_seconds=0)
    cache_key_client = SharedHttpClient(
        TransportPolicy(
            allowed_hosts=("example.test",),
            rate_limit_interval=0,
            stale_if_error_seconds=60,
        ),
        session=FakeSession([FakeResponse(304, body=b"", headers={"ETag": '"v1"'})]),
        cache=cache,
    )
    request = request_for(cacheable=True)
    key = request.cache_key()
    from nanojuris.transport.models import TransportResponse

    cache.put(
        key,
        TransportResponse(
            status_code=200,
            url=request.url,
            final_url=request.url,
            headers={"ETag": '"v1"', "Content-Type": "application/json"},
            body=b'{"ok":true}',
            elapsed_ms=1.0,
        ),
    )
    response = cache_key_client.request(request)
    assert response.status_code == 200
    assert response.body == b'{"ok":true}'
    assert response.cache_status == "revalidated"


def test_transport_uses_stale_cache_only_after_source_error(tmp_path: Path) -> None:
    cache = ContentResponseCache(tmp_path / "responses", ttl_seconds=0)
    session = FakeSession([FakeResponse(503, body=b"upstream unavailable")])
    client = SharedHttpClient(
        TransportPolicy(
            allowed_hosts=("example.test",),
            rate_limit_interval=0,
            max_retries=0,
            stale_if_error_seconds=60,
        ),
        session=session,
        cache=cache,
    )
    request = request_for(cacheable=True)
    from nanojuris.transport.models import TransportResponse

    cache.put(
        request.cache_key(),
        TransportResponse(
            status_code=200,
            url=request.url,
            final_url=request.url,
            headers={"Content-Type": "application/json"},
            body=b"cached",
            elapsed_ms=1.0,
        ),
    )
    response = client.request(request)
    assert response.status_code == 200
    assert response.body == b"cached"
    assert response.cache_status == "stale_if_error"


def test_transport_cache_bounds_body_and_supports_invalidation(tmp_path: Path) -> None:
    cache = ContentResponseCache(tmp_path / "responses", max_body_bytes=3)
    from nanojuris.transport.models import TransportResponse

    envelope = TransportResponse(
        status_code=200,
        url="https://example.test/api",
        final_url="https://example.test/api",
        headers={},
        body=b"1234",
        elapsed_ms=1.0,
    )
    with pytest.raises(ValueError, match="max_body_bytes"):
        cache.put("c" * 64, envelope)
    envelope = TransportResponse(
        status_code=200,
        url="https://example.test/api",
        final_url="https://example.test/api",
        headers={},
        body=b"123",
        elapsed_ms=1.0,
    )
    key = "c" * 64
    cache.put(key, envelope)
    assert cache.get(key) is not None
    assert cache.invalidate(key) is True
    assert cache.invalidate(key) is False


def test_transport_cache_cleanup_is_age_and_size_bounded(tmp_path: Path) -> None:
    cache = ContentResponseCache(tmp_path / "responses")
    from nanojuris.transport.models import TransportResponse

    def save(key: str, body: bytes) -> Path:
        return cache.put(
            key,
            TransportResponse(
                status_code=200,
                url="https://example.test/api",
                final_url="https://example.test/api",
                headers={},
                body=body,
                elapsed_ms=1.0,
            ),
        )

    old_path = save("d" * 64, b"old")
    new_path = save("e" * 64, b"new")
    import os

    os.utime(old_path, (100, 100))
    os.utime(new_path, (200, 200))
    report = cache.cleanup(max_age_seconds=50, now=200)
    assert report["deleted_files"] == 1
    assert cache.get("d" * 64) is None
    assert cache.get("e" * 64) is not None

    report = cache.cleanup(max_bytes=0, now=200)
    assert report["deleted_files"] == 1
    assert cache.get("e" * 64) is None


def test_transport_cache_put_enforces_global_byte_budget(tmp_path: Path) -> None:
    cache = ContentResponseCache(tmp_path / "responses", max_total_bytes=180)
    from nanojuris.transport.models import TransportResponse

    def save(key: str, body: bytes) -> None:
        cache.put(
            key,
            TransportResponse(
                status_code=200,
                url="https://example.test/api",
                final_url="https://example.test/api",
                headers={},
                body=body,
                elapsed_ms=1.0,
            ),
        )

    save("a" * 64, b"a" * 80)
    save("b" * 64, b"b" * 80)
    assert len(list((tmp_path / "responses").glob("**/*.json"))) <= 1


def test_document_reference_requires_https() -> None:
    with pytest.raises(ValueError):
        DocumentReference("doc", "test", "http://example.test/doc")


def test_content_addressed_document_cache_is_deterministic(tmp_path: Path) -> None:
    cache = ContentAddressedDocumentCache(tmp_path / "documents")
    digest = cache.put(b"public document", metadata={"source": "test"})
    assert cache.put(b"public document", metadata={"source": "changed"}) == digest
    assert cache.get(digest) == b"public document"
    assert cache.metadata(digest)["byte_size"] == len(b"public document")


def test_fetch_document_reference_is_explicit_and_traced(tmp_path: Path) -> None:
    session = FakeSession(
        [
            FakeResponse(
                200,
                body=b"<html><body>inteiro teor</body></html>",
                headers={"Content-Type": "text/html"},
            )
        ]
    )
    reference = DocumentReference(
        id="doc-1",
        source="test",
        url="https://example.test/doc",
        expected_content_types=("text/html",),
    )
    document = fetch_document_reference(
        reference,
        policy=TransportPolicy(allowed_hosts=("example.test",), rate_limit_interval=0),
        session=session,
        document_cache=ContentAddressedDocumentCache(tmp_path / "documents"),
    )
    assert document.id == "doc-1"
    assert document.text == "inteiro teor"
    assert document.source_trace is not None
    assert document.source_trace.transformations[:2] == [
        "transport_shared",
        "content_addressed_cache",
    ]


def test_fetch_document_reference_rejects_unexpected_format() -> None:
    session = FakeSession(
        [FakeResponse(200, body=b"plain", headers={"Content-Type": "text/plain"})]
    )
    reference = DocumentReference(
        id="doc-1",
        source="test",
        url="https://example.test/doc",
        expected_content_types=("application/pdf",),
    )
    with pytest.raises(ParserContractChangedError, match="outside the reference contract"):
        fetch_document_reference(
            reference,
            policy=TransportPolicy(allowed_hosts=("example.test",), rate_limit_interval=0),
            session=session,
        )


def test_fetch_document_reference_rejects_pdf_error_body_with_http_200() -> None:
    session = FakeSession(
        [
            FakeResponse(
                200,
                body=b"Erro ao tentar recuperar PDF: Falha ao recuperar arquivo do SitDoc.",
                headers={"Content-Type": "application/pdf;charset=UTF-8"},
            )
        ]
    )
    reference = DocumentReference(
        id="doc-invalid-pdf",
        source="test",
        url="https://example.test/doc-invalid-pdf",
        expected_content_types=("application/pdf", "application/octet-stream"),
    )
    with pytest.raises(ParserContractChangedError, match="structural validation"):
        fetch_document_reference(
            reference,
            policy=TransportPolicy(allowed_hosts=("example.test",), rate_limit_interval=0),
            session=session,
        )
