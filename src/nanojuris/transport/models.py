"""Typed contracts for the shared provider transport."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from nanojuris.governance import DEFAULT_OPERATIONAL_POLICY


class TransportStatus(str, Enum):
    """Transport outcome independent from parser semantics."""

    COMPLETE = "complete"
    TIMEOUT = "timeout"
    TLS_ERROR = "tls_error"
    SOURCE_UNAVAILABLE = "source_unavailable"
    REDIRECT_LIMIT = "redirect_limit"
    REDIRECT_OUTSIDE_ALLOWLIST = "redirect_outside_allowlist"
    RESPONSE_TOO_LARGE = "response_too_large"
    CIRCUIT_OPEN = "circuit_open"


@dataclass(frozen=True, slots=True)
class TransportPolicy:
    """Conservative defaults shared by provider adapters."""

    allowed_hosts: tuple[str, ...] = ()
    timeout_seconds: float = 20.0
    max_bytes: int = 4_000_000
    max_redirects: int = 3
    max_retries: int = 2
    base_delay_seconds: float = 0.25
    rate_limit_interval: float = DEFAULT_OPERATIONAL_POLICY.min_provider_request_interval_seconds
    cache_ttl_seconds: float | None = DEFAULT_OPERATIONAL_POLICY.live_cache_ttl_seconds
    stale_if_error_seconds: float = 0.0
    user_agent: str = "NanoJuris/0.4 (+https://github.com/ndtj/nanojuris)"
    verify_ssl: bool = True
    # Requests/urllib3 uses HTTP/1.1 for this adapter.  Keeping the negotiated
    # version explicit prevents a provider fallback from silently changing the
    # TLS policy or enabling an unbounded alternate protocol.
    http_version: str = "1.1"

    def __post_init__(self) -> None:
        hosts = tuple(sorted({self._normalize_host(item) for item in self.allowed_hosts if item}))
        object.__setattr__(self, "allowed_hosts", hosts)
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        if self.max_redirects < 0 or self.max_retries < 0:
            raise ValueError("redirect and retry limits must be non-negative")
        if self.base_delay_seconds < 0 or self.rate_limit_interval < 0:
            raise ValueError("delay values must be non-negative")
        if self.cache_ttl_seconds is not None and self.cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds must be non-negative")
        if self.stale_if_error_seconds < 0:
            raise ValueError("stale_if_error_seconds must be non-negative")
        if not self.user_agent.strip():
            raise ValueError("user_agent must not be empty")
        if self.http_version != "1.1":
            raise ValueError("only the bounded HTTP/1.1 transport is supported")

    @staticmethod
    def _normalize_host(value: str) -> str:
        host = value.strip().lower().rstrip(".")
        if "://" in host:
            host = urlparse(host).hostname or ""
        return host

    def allows(self, url: str) -> bool:
        """Return whether *url* is an HTTPS public host in the allowlist."""

        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.username or parsed.password:
            return False
        hostname = (parsed.hostname or "").lower().rstrip(".")
        if not hostname:
            return False
        return any(hostname == host or hostname.endswith(f".{host}") for host in self.allowed_hosts)


@dataclass(frozen=True, slots=True)
class TransportRequest:
    """One bounded request; query/body are retained only in redacted form."""

    source: str
    operation: str
    method: str
    url: str
    params: dict[str, Any] = field(default_factory=dict)
    data: Any = None
    json_body: Any = None
    headers: dict[str, str] = field(default_factory=dict)
    idempotent: bool | None = None
    cacheable: bool = False
    # Bump when the representation or parser contract changes.  Including
    # this value in the digest prevents a stale response from an older
    # transport/parser contract being reused accidentally.  It is a namespace
    # marker only; the cache never becomes a searchable document corpus.
    cache_version: str = "live-response-v1"

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.operation.strip():
            raise ValueError("source and operation must not be empty")
        if self.method.upper() not in {"GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"}:
            raise ValueError("unsupported HTTP method")
        if not self.url.strip():
            raise ValueError("url must not be empty")
        if not self.cache_version.strip() or len(self.cache_version) > 64:
            raise ValueError("cache_version must be a non-empty short value")

    @property
    def effective_idempotent(self) -> bool:
        if self.idempotent is not None:
            return self.idempotent
        return self.method.upper() in {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}

    def cache_key(self) -> str:
        material = {
            "source": self.source,
            "operation": self.operation,
            "method": self.method.upper(),
            "url": self.url,
            "params": self.params,
            "data": self.data,
            "json": self.json_body,
            "cache_version": self.cache_version,
        }
        encoded = json.dumps(material, sort_keys=True, ensure_ascii=False, default=str).encode()
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class TransportResponse:
    """Immutable response envelope; ``body`` is intentionally excluded from repr."""

    status_code: int | None
    url: str
    final_url: str | None
    headers: dict[str, str]
    body: bytes = field(repr=False, compare=False)
    elapsed_ms: float
    redirects: tuple[dict[str, str | int], ...] = ()
    status: TransportStatus = TransportStatus.COMPLETE
    error_type: str | None = None
    error: str | None = None
    content_sha256: str = ""
    cache_status: str | None = None

    def __post_init__(self) -> None:
        if not self.content_sha256:
            object.__setattr__(self, "content_sha256", hashlib.sha256(self.body).hexdigest())
        if self.elapsed_ms < 0:
            raise ValueError("elapsed_ms must be non-negative")

    @property
    def content_type(self) -> str | None:
        value = self.headers.get("Content-Type") or self.headers.get("content-type")
        return value or None

    @property
    def byte_size(self) -> int:
        return len(self.body)

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.text)
