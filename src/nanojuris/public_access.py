"""Ordinary public-session helpers with no stealth or challenge bypass."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import requests

from nanojuris.access import AccessPath
from nanojuris.governance import DEFAULT_OPERATIONAL_POLICY
from nanojuris.transport import (
    SharedHttpClient,
    TransportPolicy,
    TransportRequest,
    TransportResponse,
)

_CSRF_PATTERNS = (
    re.compile(r'<meta[^>]+name=["\']csrf-token["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(
        r'<input[^>]+name=["\'](?:csrfmiddlewaretoken|_token|authenticity_token)'
        r'["\'][^>]+value=["\']([^"\']+)',
        re.I,
    ),
)


def extract_csrf_token(html: str) -> str | None:
    """Extract a normal-flow CSRF token without storing or transmitting it."""

    for pattern in _CSRF_PATTERNS:
        match = pattern.search(html)
        if match:
            token = match.group(1).strip()
            if token and len(token) <= 4096:
                return token
    return None


@dataclass(slots=True)
class PublicSession:
    """Ephemeral in-memory public session backed by shared transport."""

    path: AccessPath
    session: requests.Session
    transport: SharedHttpClient

    @classmethod
    def create(
        cls,
        path: AccessPath,
        *,
        session: requests.Session | None = None,
        max_retries: int = 2,
        rate_limit_interval: float = (
            DEFAULT_OPERATIONAL_POLICY.min_provider_request_interval_seconds
        ),
    ) -> PublicSession:
        if max_retries < 0 or rate_limit_interval < 0:
            raise ValueError("invalid public-session retry/rate budget")
        active_session = session or requests.Session()
        policy = TransportPolicy(
            allowed_hosts=path.allowed_hosts,
            timeout_seconds=path.timeout_seconds,
            max_bytes=path.max_bytes,
            max_redirects=path.max_redirects,
            max_retries=max_retries,
            rate_limit_interval=rate_limit_interval,
            http_version="1.1",
        )
        return cls(path, active_session, SharedHttpClient(policy, session=active_session))

    def request(
        self,
        method: str,
        url: str,
        *,
        operation: str = "public_session",
        params: dict[str, Any] | None = None,
        data: Any = None,
        json_body: Any = None,
        headers: dict[str, str] | None = None,
        csrf_token: str | None = None,
        cacheable: bool = False,
    ) -> TransportResponse:
        if not self.path.allows(url):
            raise ValueError("public-session URL is outside the allowlist")
        request_headers = dict(headers or {})
        if csrf_token:
            if len(csrf_token) > 4096:
                raise ValueError("csrf_token is too long")
            request_headers.setdefault("X-CSRF-TOKEN", csrf_token)
        return self.transport.request(
            TransportRequest(
                source=self.path.provider,
                operation=operation,
                method=method,
                url=url,
                params=params or {},
                data=data,
                json_body=json_body,
                headers=request_headers,
                cacheable=cacheable,
            )
        )

    def close(self) -> None:
        self.session.close()


@dataclass(slots=True)
class PublicChromium:
    """Explicitly ordinary Playwright Chromium lifecycle."""

    _playwright: Any
    browser: Any

    @classmethod
    def start(cls, *, headless: bool = True) -> PublicChromium:
        try:
            from playwright.sync_api import sync_playwright
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("install the qa extra to use public Chromium") from exc
        playwright = sync_playwright().start()
        # No stealth flags, proxy rotation, fingerprint changes, or challenge
        # solvers are supplied. The caller must close the returned browser.
        browser = playwright.chromium.launch(headless=headless)
        return cls(playwright, browser)

    def close(self) -> None:
        self.browser.close()
        self._playwright.stop()


__all__ = ["PublicChromium", "PublicSession", "extract_csrf_token"]
