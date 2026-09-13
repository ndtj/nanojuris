from __future__ import annotations

import requests

from nanojuris.http_retry import request_with_retries


class Response:
    def __init__(self, status_code: int, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self.headers = headers or {}


def test_retry_honors_retry_after_and_stops_at_success() -> None:
    responses = iter(
        [
            Response(503, {"Retry-After": "0.01"}),
            Response(429),
            Response(200),
        ]
    )
    delays: list[float] = []

    result = request_with_retries(lambda: next(responses), sleep_fn=delays.append)

    assert result.status_code == 200
    assert delays == [0.01, 0.5]


def test_retry_does_not_repeat_access_control_status() -> None:
    calls = 0

    def request() -> Response:
        nonlocal calls
        calls += 1
        return Response(403)

    result = request_with_retries(request, sleep_fn=lambda _: None)

    assert result.status_code == 403
    assert calls == 1


def test_retry_rethrows_final_transport_error() -> None:
    calls = 0

    def request() -> Response:
        nonlocal calls
        calls += 1
        raise requests.ConnectionError("offline")

    try:
        request_with_retries(request, sleep_fn=lambda _: None)
    except requests.ConnectionError as exc:
        assert str(exc) == "offline"
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("transport error was swallowed")
    assert calls == 3


def test_non_idempotent_request_is_never_retried() -> None:
    calls = 0

    def request() -> Response:
        nonlocal calls
        calls += 1
        return Response(503)

    result = request_with_retries(request, idempotent=False, sleep_fn=lambda _: None)

    assert result.status_code == 503
    assert calls == 1


def test_jitter_is_bounded_and_injectable() -> None:
    responses = iter([Response(503), Response(200)])
    delays: list[float] = []

    request_with_retries(
        lambda: next(responses),
        sleep_fn=delays.append,
        jitter_fn=lambda value: value + 0.1,
    )

    assert delays == [0.35]


def test_retry_after_is_never_shortened_by_local_five_second_backoff() -> None:
    responses = iter([Response(503, {"Retry-After": "12"}), Response(200)])
    delays: list[float] = []
    request_with_retries(lambda: next(responses), sleep_fn=delays.append)
    assert delays == [12.0]
