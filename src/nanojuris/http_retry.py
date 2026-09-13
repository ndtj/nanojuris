"""Small, bounded retry policy for public provider requests."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import requests

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def request_with_retries(
    request_fn: Callable[[], Any],
    *,
    max_retries: int = 2,
    base_delay: float = 0.25,
    sleep_fn: Callable[[float], None] = time.sleep,
    idempotent: bool = True,
    jitter_fn: Callable[[float], float] | None = None,
) -> Any:
    """Call a requests-compatible function with a bounded transient policy.

    Retries are enabled by default for backwards compatibility with the
    existing GET-only callers.  Non-idempotent operations must pass
    ``idempotent=False`` so a transient response or connection failure cannot
    duplicate a write. ``jitter_fn`` is injectable for deterministic tests and
    can add bounded jitter in a production runner.
    """

    retries = max(0, int(max_retries))
    last_response: Any | None = None
    last_error: requests.RequestException | None = None
    for attempt in range(retries + 1):
        try:
            response = request_fn()
        except requests.RequestException as exc:
            last_error = exc
            if not idempotent or attempt >= retries:
                raise
            sleep_fn(_delay(_backoff(attempt, base_delay=base_delay), jitter_fn))
            continue
        except (AssertionError, IndexError):
            if last_error is not None:
                raise last_error from None
            if last_response is not None:
                return last_response
            raise

        last_response = response
        status = int(getattr(response, "status_code", 0) or 0)
        if not idempotent or status not in RETRYABLE_STATUS_CODES or attempt >= retries:
            return response
        sleep_fn(
            _delay(
                _retry_after(response, fallback=_backoff(attempt, base_delay=base_delay)),
                jitter_fn,
            )
        )
    return last_response


def _backoff(attempt: int, *, base_delay: float) -> float:
    return max(0.0, min(float(base_delay) * (2**attempt), 5.0))


def _retry_after(response: Any, *, fallback: float) -> float:
    headers = getattr(response, "headers", {}) or {}
    value = headers.get("Retry-After") or headers.get("retry-after")
    try:
        parsed = float(str(value))
    except (TypeError, ValueError):
        return fallback
    # Retry-After is an instruction from the public source.  Do not shorten
    # it merely to fit the local exponential backoff ceiling.
    return max(0.0, parsed)


def _delay(value: float, jitter_fn: Callable[[float], float] | None) -> float:
    """Apply caller-provided jitter without allowing an invalid delay."""

    # Jitter may lengthen a delay but must never shorten an explicit
    # Retry-After instruction from the source.
    jittered = value if jitter_fn is None else max(value, float(jitter_fn(value)))
    return max(0.0, float(jittered))
