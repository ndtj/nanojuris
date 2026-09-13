"""Bounded, retry-aware HTTP client shared by public providers."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import replace
from threading import Lock
from urllib.parse import urljoin, urlparse

import requests

from nanojuris.errors import SourceUnavailableError, safe_error_message
from nanojuris.transport.cache import ContentResponseCache
from nanojuris.transport.circuit import CircuitBreaker
from nanojuris.transport.models import (
    TransportPolicy,
    TransportRequest,
    TransportResponse,
    TransportStatus,
)
from nanojuris.transport.redaction import redact_headers, redact_url

_RETRYABLE = frozenset({429, 500, 502, 503, 504})


class SharedHttpClient:
    """Safe transport boundary; parsers receive only ``TransportResponse``."""

    def __init__(
        self,
        policy: TransportPolicy,
        *,
        session: requests.Session | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        cache: ContentResponseCache | None = None,
    ) -> None:
        self.policy = policy
        self.session = session or requests.Session()
        if hasattr(self.session, "trust_env"):
            self.session.trust_env = False
        headers = getattr(self.session, "headers", None)
        if headers is not None and hasattr(headers, "update"):
            headers.update({"User-Agent": policy.user_agent})
        self._sleep = sleep_fn
        self._clock = clock
        self._last_request: defaultdict[str, float] = defaultdict(float)
        # A provider federation may execute sources concurrently, but requests
        # to one public host are serialized.  This is stronger than merely
        # spacing timestamps and prevents overlapping retries/page probes.
        self._host_locks: defaultdict[str, Lock] = defaultdict(Lock)
        self._circuits: dict[tuple[str, str], CircuitBreaker] = {}
        self._cache = cache
        if self._cache is not None and self._cache.ttl_seconds is None:
            # Direct cache users retain the historical unbounded semantics;
            # live transport clients opt into the governance TTL explicitly.
            self._cache.ttl_seconds = policy.cache_ttl_seconds

    def request(self, request: TransportRequest) -> TransportResponse:
        """Perform one bounded request, retrying only transient idempotent errors."""

        host = (urlparse(request.url).hostname or "").lower()
        with self._host_locks[host]:
            return self._request_serialized(request)

    def _request_serialized(self, request: TransportRequest) -> TransportResponse:
        """Execute a request while the caller owns its host serialization lock."""

        if not self.policy.allows(request.url):
            raise ValueError(f"URL fora da allowlist de transporte: {redact_url(request.url)}")
        circuit = self._circuits.setdefault(
            (request.source, request.operation), CircuitBreaker(clock=self._clock)
        )
        if not circuit.allow():
            return TransportResponse(
                status_code=None,
                url=request.url,
                final_url=None,
                headers={},
                body=b"",
                elapsed_ms=0.0,
                status=TransportStatus.CIRCUIT_OPEN,
                error_type="circuit_open",
                error="circuit breaker is open",
            )
        cache_key = request.cache_key() if request.cacheable and self._cache else None
        stale_cached: TransportResponse | None = None
        effective_request = request
        if cache_key and self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
            if self.policy.stale_if_error_seconds > 0:
                stale_cached = self._cache.get_stale(
                    cache_key,
                    max_age_seconds=self.policy.stale_if_error_seconds,
                )
                if stale_cached is not None and request.method.upper() in {"GET", "HEAD"}:
                    conditional_headers = dict(request.headers)
                    etag = stale_cached.headers.get("ETag") or stale_cached.headers.get("etag")
                    last_modified = stale_cached.headers.get("Last-Modified")
                    if not last_modified:
                        last_modified = stale_cached.headers.get("last-modified")
                    if etag:
                        conditional_headers.setdefault("If-None-Match", etag)
                    if last_modified:
                        conditional_headers.setdefault("If-Modified-Since", last_modified)
                    if conditional_headers != request.headers:
                        effective_request = replace(request, headers=conditional_headers)

        attempts = self.policy.max_retries if request.effective_idempotent else 0
        response: TransportResponse | None = None
        for attempt in range(attempts + 1):
            self._respect_budget(request.url)
            try:
                response = self._single_request(effective_request)
            except requests.exceptions.Timeout as exc:
                circuit.record_failure()
                if attempt >= attempts:
                    if stale_cached is not None:
                        return _stale_response(stale_cached)
                    raise SourceUnavailableError("provider request failed: timeout") from exc
                self._sleep(self._backoff(attempt))
                continue
            except requests.exceptions.SSLError as exc:
                circuit.record_failure()
                raise SourceUnavailableError("provider TLS negotiation failed") from exc
            except requests.RequestException as exc:
                circuit.record_failure()
                if attempt >= attempts:
                    if stale_cached is not None:
                        return _stale_response(stale_cached)
                    raise SourceUnavailableError(
                        f"provider request failed: {safe_error_message(exc)}"
                    ) from exc
                self._sleep(self._backoff(attempt))
                continue

            if response.status_code in _RETRYABLE and attempt < attempts:
                circuit.record_failure()
                self._sleep(self._retry_after(response, self._backoff(attempt)))
                continue
            if response.status_code is not None and response.status_code < 500:
                circuit.record_success()
            elif response.status_code is not None and response.status_code >= 500:
                circuit.record_failure()
            if response.status is not TransportStatus.COMPLETE:
                circuit.record_failure()
            break

        if response is None:  # pragma: no cover - defensive
            if stale_cached is not None:
                return _stale_response(stale_cached)
            raise SourceUnavailableError("provider request returned no response")
        if response.status_code == 304 and stale_cached is not None:
            merged_headers = dict(stale_cached.headers)
            merged_headers.update(response.headers)
            response = replace(
                stale_cached,
                status_code=200,
                headers=merged_headers,
                final_url=response.final_url or stale_cached.final_url,
                elapsed_ms=response.elapsed_ms,
                redirects=response.redirects,
                cache_status="revalidated",
            )
        elif stale_cached is not None and (
            response.status is not TransportStatus.COMPLETE
            or (response.status_code is not None and response.status_code >= 500)
        ):
            return _stale_response(stale_cached)
        if cache_key and self._cache is not None and response.status is TransportStatus.COMPLETE:
            self._cache.put(cache_key, response)
        return response

    def _single_request(self, request: TransportRequest) -> TransportResponse:
        current_url = request.url
        redirects: list[dict[str, str | int]] = []
        started = time.perf_counter()
        raw_response: requests.Response | None = None
        body = b""
        status = TransportStatus.COMPLETE
        error_type: str | None = None
        error: str | None = None
        try:
            for _ in range(self.policy.max_redirects + 1):
                if not self.policy.allows(current_url):
                    status = TransportStatus.REDIRECT_OUTSIDE_ALLOWLIST
                    error_type = status.value
                    error = "redirect target is outside the configured allowlist"
                    break
                raw_response = self.session.request(
                    request.method.upper(),
                    current_url,
                    params=request.params or None,
                    data=request.data,
                    json=request.json_body,
                    headers=request.headers,
                    timeout=self.policy.timeout_seconds,
                    verify=self.policy.verify_ssl,
                    allow_redirects=False,
                    stream=True,
                )
                response_headers = getattr(raw_response, "headers", {}) or {}
                location = response_headers.get("Location")
                if getattr(raw_response, "is_redirect", False) and location:
                    redirects.append(
                        {
                            "status": raw_response.status_code,
                            "url": redact_url(current_url),
                            "location": redact_url(urljoin(current_url, location)),
                        }
                    )
                    current_url = urljoin(current_url, location)
                    close = getattr(raw_response, "close", None)
                    if callable(close):
                        close()
                    continue
                body, exceeded = _read_bounded(raw_response, self.policy.max_bytes)
                if exceeded:
                    status = TransportStatus.RESPONSE_TOO_LARGE
                    error_type = status.value
                    error = "response exceeded the configured byte limit"
                break
            else:
                status = TransportStatus.REDIRECT_LIMIT
                error_type = status.value
                error = "redirect limit exceeded"
        finally:
            if raw_response is not None:
                close = getattr(raw_response, "close", None)
                if callable(close):
                    close()

        elapsed_ms = (time.perf_counter() - started) * 1000
        headers = redact_headers(
            getattr(raw_response, "headers", {}) if raw_response is not None else {}
        )
        return TransportResponse(
            status_code=(
                raw_response.status_code
                if raw_response is not None
                and status is not TransportStatus.REDIRECT_OUTSIDE_ALLOWLIST
                and status is not TransportStatus.REDIRECT_LIMIT
                else None
            ),
            url=request.url,
            final_url=current_url
            if raw_response is not None and status is TransportStatus.COMPLETE
            else None,
            headers=headers,
            body=body,
            elapsed_ms=round(elapsed_ms, 2),
            redirects=tuple(redirects),
            status=status,
            error_type=error_type,
            error=error,
        )

    def _respect_budget(self, url: str) -> None:
        host = (urlparse(url).hostname or "").lower()
        elapsed = self._clock() - self._last_request[host]
        if elapsed < self.policy.rate_limit_interval:
            self._sleep(self.policy.rate_limit_interval - elapsed)
        self._last_request[host] = self._clock()

    def _backoff(self, attempt: int) -> float:
        return min(max(self.policy.base_delay_seconds, 0.0) * (2**attempt), 5.0)

    @staticmethod
    def _retry_after(response: TransportResponse, fallback: float) -> float:
        value = response.headers.get("Retry-After") or response.headers.get("retry-after")
        try:
            # A server-provided Retry-After is authoritative.  The local
            # exponential fallback remains bounded, but an explicit delay is
            # never shortened (shortening it can violate the source policy).
            return max(0.0, float(str(value)))
        except (TypeError, ValueError):
            return fallback


def _stale_response(response: TransportResponse) -> TransportResponse:
    """Return a bounded stale response with an explicit cache disposition."""

    return replace(response, cache_status="stale_if_error")


def _read_bounded(response: requests.Response, maximum: int) -> tuple[bytes, bool]:
    chunks: list[bytes] = []
    remaining = maximum
    exceeded = False
    iter_content = getattr(response, "iter_content", None)
    if not callable(iter_content):
        raw_content = getattr(response, "content", None)
        text = getattr(response, "text", "")
        if raw_content is None or (not raw_content and text):
            # Lightweight requests-compatible test sessions and a few public
            # adapters expose only ``text``.  Preserve that body at the
            # transport boundary instead of silently turning it into an empty
            # response.
            encoding = getattr(response, "encoding", None) or "utf-8"
            raw_content = str(text).encode(str(encoding), errors="replace")
        body = bytes(raw_content or b"")
        return body[:maximum], len(body) > maximum
    iterator = iter(iter_content(chunk_size=64 * 1024))
    for chunk in iterator:
        if not chunk:
            continue
        if len(chunk) > remaining:
            chunks.append(chunk[:remaining])
            exceeded = True
            break
        chunks.append(chunk)
        remaining -= len(chunk)
        if remaining == 0:
            # Probe one more chunk so an exact-limit response is accepted while
            # a larger response is classified explicitly.
            try:
                extra = next(iterator, b"")
            except StopIteration:  # pragma: no cover - iterator contract
                extra = b""
            exceeded = bool(extra)
            break
    return b"".join(chunks), exceeded
