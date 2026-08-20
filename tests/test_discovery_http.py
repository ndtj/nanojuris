from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
import requests

from nanojuris.discovery.http import (
    HttpDiscoveryClient,
    _access_status,
    _extraction_status,
    _status_from_response,
    _status_from_transport,
)
from nanojuris.discovery.models import (
    DiscoveryPolicy,
    DiscoveryRequest,
    DiscoveryResponse,
    DiscoveryStatus,
)
from nanojuris.models import AccessStatus, ExtractionStatus

HTML = b"""
<html><body>
<a href='/jurisprudencia/123'>decisao</a>
<form action='/api/search' method='post'><input name='termo'></form>
<p id='ementa'>Ementa e inteiro teor da decisao</p>
</body></html>
"""


class FakeSession:
    def __init__(self, responses: list[requests.Response | Exception]) -> None:
        self.responses = list(responses)
        self.headers: dict[str, str] = {}
        self.trust_env = True
        self.calls: list[tuple[str, str]] = []

    def request(self, method: str, url: str, **kwargs: object) -> requests.Response:
        self.calls.append((method, url))
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def get(self, url: str, **kwargs: object) -> requests.Response:
        return self.request("GET", url, **kwargs)


def response(
    status_code: int,
    body: bytes = b"",
    *,
    content_type: str = "text/html; charset=utf-8",
    location: str | None = None,
) -> requests.Response:
    result = requests.Response()
    result.status_code = status_code
    result.url = "https://example.test/source"
    result.headers["Content-Type"] = content_type
    if location is not None:
        result.headers["Location"] = location
    result._content = body
    result._content_consumed = True
    return result


def client(
    session: FakeSession,
    *,
    max_redirects: int = 3,
    max_bytes_per_response: int = 1024 * 1024,
    respect_robots: bool = False,
    cache_dir: str | None = None,
) -> HttpDiscoveryClient:
    return HttpDiscoveryClient(
        DiscoveryPolicy(
            ("example.test",),
            max_redirects=max_redirects,
            max_bytes_per_response=max_bytes_per_response,
            respect_robots=respect_robots,
            delay_seconds=0,
        ),
        session=session,
        cache_dir=cache_dir,
    )


def test_fetch_extracts_contract_and_redacts_request_payload():
    session = FakeSession([response(200, HTML)])
    evidence = client(session).fetch(
        run_id="run-1",
        seed_url="https://example.test/seed",
        request=DiscoveryRequest(
            "POST",
            "https://example.test/search",
            query={"page": 1},
            body={"term": "acesso", "password": "secret"},
            headers={"Authorization": "Bearer token"},
        ),
    )

    assert evidence.status is DiscoveryStatus.VALID
    assert evidence.access_status is AccessStatus.PUBLIC
    assert evidence.extraction_status is ExtractionStatus.COMPLETE
    assert evidence.route_candidates
    assert evidence.filter_candidates
    assert evidence.selector_candidates
    assert evidence.request.body["password"] == "<redacted>"
    assert evidence.request.headers["Authorization"] == "<redacted>"
    assert session.calls == [("POST", "https://example.test/search")]


def test_discover_follows_allowed_redirects_and_records_trace():
    session = FakeSession([response(302, location="/login"), response(200, HTML)])
    run = client(session).discover("https://example.test/start")
    evidence = run.evidences[0]

    assert evidence.status is DiscoveryStatus.VALID
    assert evidence.response.final_url == "https://example.test/login"
    assert evidence.response.redirects == [
        {
            "status": 302,
            "url": "https://example.test/start",
            "location": "/login",
        }
    ]
    assert run.finished_at is not None


def test_fetch_classifies_transport_failures_without_calling_them_empty():
    cases: list[tuple[Exception, DiscoveryStatus]] = [
        (requests.exceptions.Timeout("slow"), DiscoveryStatus.TIMEOUT),
        (requests.exceptions.SSLError("bad certificate"), DiscoveryStatus.TLS_ERROR),
        (
            requests.exceptions.ConnectionError("offline"),
            DiscoveryStatus.SOURCE_UNAVAILABLE,
        ),
    ]
    for error, expected in cases:
        evidence = client(FakeSession([error])).fetch(
            run_id="run-1",
            seed_url="https://example.test/source",
            request=DiscoveryRequest("GET", "https://example.test/source"),
        )
        assert evidence.status is expected
        assert evidence.response.transport_status != "complete"
        assert evidence.extraction_status is ExtractionStatus.EMPTY


def test_fetch_stops_at_redirect_limit():
    session = FakeSession([response(302, location="/next") for _ in range(3)])
    evidence = client(session, max_redirects=2).fetch(
        run_id="run-1",
        seed_url="https://example.test/source",
        request=DiscoveryRequest("GET", "https://example.test/source"),
    )

    assert evidence.status is DiscoveryStatus.SOURCE_UNAVAILABLE
    assert evidence.response.error_type == "redirect_limit"
    assert len(evidence.response.redirects) == 3


def test_fetch_bounds_large_response_body():
    evidence = client(
        FakeSession([response(200, b"0123456789")]),
        max_bytes_per_response=4,
    ).fetch(
        run_id="run-1",
        seed_url="https://example.test/source",
        request=DiscoveryRequest("GET", "https://example.test/source"),
    )

    assert evidence.response.body == b"0123"
    assert "bounded" in evidence.limitations[0]


def test_robots_policy_handles_not_found_disallow_and_network_failure():
    allowed = client(
        FakeSession([response(404)]),
        respect_robots=True,
    )
    assert allowed._can_fetch("https://example.test/source") is True
    assert allowed._can_fetch("https://example.test/source") is True
    assert len(allowed.session.calls) == 1

    disallowed = client(
        FakeSession([response(200, b"User-agent: *\nDisallow: /")]),
        respect_robots=True,
    )
    assert disallowed._can_fetch("https://example.test/source") is False

    failed = client(
        FakeSession([requests.exceptions.ConnectionError("offline")]),
        respect_robots=True,
    )
    assert failed._can_fetch("https://example.test/source") is False


def test_robots_disallowed_is_explicit_evidence():
    session = FakeSession([response(200, b"User-agent: *\nDisallow: /")])
    evidence = client(session, respect_robots=True).fetch(
        run_id="run-1",
        seed_url="https://example.test/source",
        request=DiscoveryRequest("GET", "https://example.test/source"),
    )

    assert evidence.status is DiscoveryStatus.ROBOTS_DISALLOWED
    assert evidence.response.transport_status == "robots_disallowed"
    assert session.calls == [("GET", "https://example.test/robots.txt")]


def test_cache_replays_without_a_second_http_request():
    cache_dir = Path(".tmp") / f"discovery-http-{uuid4().hex}"
    first_session = FakeSession([response(200, HTML)])
    try:
        first = client(first_session, cache_dir=str(cache_dir)).fetch(
            run_id="run-1",
            seed_url="https://example.test/source",
            request=DiscoveryRequest("GET", "https://example.test/source"),
        )
        second_session = FakeSession([])
        second = client(second_session, cache_dir=str(cache_dir)).fetch(
            run_id="run-2",
            seed_url="https://example.test/seed",
            request=DiscoveryRequest("GET", "https://example.test/source"),
        )

        assert first.status is DiscoveryStatus.VALID
        assert second.source == "cache"
        assert second.run_id == "run-2"
        assert second.seed_url == "https://example.test/seed"
        assert second_session.calls == []
    finally:
        for child in cache_dir.glob("*"):
            child.unlink()
        if cache_dir.exists():
            cache_dir.rmdir()


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (401, DiscoveryStatus.ACCESS_CONTROLLED),
        (403, DiscoveryStatus.ACCESS_CONTROLLED),
        (429, DiscoveryStatus.RATE_LIMITED),
        (404, DiscoveryStatus.EMPTY),
        (503, DiscoveryStatus.SOURCE_UNAVAILABLE),
        (302, DiscoveryStatus.UNKNOWN),
    ],
)
def test_status_mapping_preserves_access_and_source_diagnostics(
    status_code: int, expected: DiscoveryStatus
):
    mapped = _status_from_response(
        DiscoveryResponse(status_code=status_code, url="https://example.test")
    )
    assert mapped is expected


def test_status_and_metadata_helpers_cover_terminal_states():
    assert _status_from_transport("timeout") is DiscoveryStatus.TIMEOUT
    assert _status_from_transport("tls_error") is DiscoveryStatus.TLS_ERROR
    assert _status_from_transport("source_unavailable") is DiscoveryStatus.SOURCE_UNAVAILABLE
    assert _status_from_transport("redirect_limit") is DiscoveryStatus.SOURCE_UNAVAILABLE
    assert (
        _status_from_transport("redirect_outside_allowlist")
        is DiscoveryStatus.REDIRECT_OUTSIDE_ALLOWLIST
    )
    assert _status_from_transport("other") is DiscoveryStatus.UNKNOWN

    assert _access_status(DiscoveryStatus.ACCESS_CONTROLLED) is AccessStatus.ACCESS_CONTROL_REQUIRED
    assert (
        _access_status(DiscoveryStatus.REDIRECT_OUTSIDE_ALLOWLIST)
        is AccessStatus.ACCESS_CONTROL_REQUIRED
    )
    assert _access_status(DiscoveryStatus.EMPTY) is AccessStatus.NOT_FOUND
    assert _access_status(DiscoveryStatus.VALID) is AccessStatus.PUBLIC
    assert _access_status(DiscoveryStatus.UNKNOWN) is AccessStatus.PARTIAL

    assert _extraction_status(DiscoveryStatus.EMPTY, True) is ExtractionStatus.EMPTY
    assert _extraction_status(DiscoveryStatus.VALID, False) is ExtractionStatus.EMPTY
    assert _extraction_status(DiscoveryStatus.ACCESS_CONTROLLED, True) is ExtractionStatus.PARTIAL
    assert _extraction_status(DiscoveryStatus.RATE_LIMITED, True) is ExtractionStatus.PARTIAL
    assert _extraction_status(DiscoveryStatus.TIMEOUT, True) is ExtractionStatus.FAILED
    assert _extraction_status(DiscoveryStatus.VALID, True) is ExtractionStatus.COMPLETE


def test_fetch_rejects_redirect_outside_policy_before_following():
    session = FakeSession([response(302, location="https://other.test/private")])
    evidence = client(session).fetch(
        run_id="run-1",
        seed_url="https://example.test/source",
        request=DiscoveryRequest("GET", "https://example.test/source"),
    )

    assert evidence.status is DiscoveryStatus.REDIRECT_OUTSIDE_ALLOWLIST
    assert evidence.response.error_type == "redirect_outside_allowlist"


def test_fetch_handles_unexpected_request_exception():
    class UnexpectedSession(FakeSession):
        def request(self, method: str, url: str, **kwargs: object) -> requests.Response:
            raise RuntimeError("unexpected")

    with pytest.raises(RuntimeError, match="unexpected"):
        client(UnexpectedSession([])).fetch(
            run_id="run-1",
            seed_url="https://example.test/source",
            request=DiscoveryRequest("GET", "https://example.test/source"),
        )


def test_policy_cache_can_be_reused_for_different_run_ids():
    cache_dir = Path(".tmp") / f"discovery-http-{uuid4().hex}"
    session = FakeSession([response(200, b"ok")])
    try:
        discovery = client(session, cache_dir=str(cache_dir))
        request = DiscoveryRequest("GET", "https://example.test/source")
        first = discovery.fetch(run_id="one", seed_url=request.url, request=request)
        second = discovery.fetch(run_id="two", seed_url=request.url, request=request)
        assert first.response.body == second.response.body == b"ok"
        assert second.source == "cache"
    finally:
        for child in cache_dir.glob("*"):
            child.unlink()
        if cache_dir.exists():
            cache_dir.rmdir()
