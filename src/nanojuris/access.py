"""Contracts for lawful, bounded access to public provider surfaces.

This module deliberately models access evidence without performing any browser
automation or trying to defeat access controls.  It is useful for adapters and
operator probes that need to distinguish a passive marker from a challenge that
actually prevented retrieval.  Session cookies, CSRF values and response
bodies are never part of the persisted contracts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse


class AccessPathKind(str, Enum):
    """Public access mechanisms supported by the runtime contract."""

    HTTP = "http"
    BROWSER = "browser"


class AccessOutcome(str, Enum):
    """Classification of one bounded access attempt."""

    SUCCESS = "success"
    AUTHORITATIVE_EMPTY = "authoritative_empty"
    PASSIVE_MARKER = "passive_marker"
    CHALLENGE_ENFORCED = "challenge_enforced"
    ACCESS_BLOCKED = "access_blocked"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    TLS_ERROR = "tls_error"
    SCHEMA_INVALID = "schema_invalid"
    TRANSPORT_ERROR = "transport_error"


@dataclass(frozen=True, slots=True)
class AccessPath:
    """Allowlisted public route and its bounded request budget."""

    provider: str
    url: str
    kind: AccessPathKind = AccessPathKind.HTTP
    allowed_hosts: tuple[str, ...] = ()
    timeout_seconds: float = 20.0
    max_bytes: int = 4_000_000
    max_redirects: int = 3

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or parsed.username or parsed.password:
            raise ValueError("access paths must use an HTTPS public URL")
        if not parsed.hostname:
            raise ValueError("access path URL must include a host")
        hosts = tuple(
            sorted({_normalize_host(host) for host in self.allowed_hosts if _normalize_host(host)})
        )
        object.__setattr__(self, "allowed_hosts", hosts)
        if not hosts:
            raise ValueError("at least one allowlisted host is required")
        if not self.allows(self.url):
            raise ValueError("access path URL is outside the host allowlist")
        if self.timeout_seconds <= 0 or self.max_bytes < 1 or self.max_redirects < 0:
            raise ValueError("invalid access budget")

    def allows(self, url: str) -> bool:
        """Return whether *url* is HTTPS and inside this path's allowlist."""

        parsed = urlparse(url)
        host = _normalize_host(parsed.hostname or "")
        return (
            parsed.scheme == "https"
            and not parsed.username
            and not parsed.password
            and bool(host)
            and any(
                host == allowed or host.endswith(f".{allowed}") for allowed in self.allowed_hosts
            )
        )


@dataclass(frozen=True, slots=True)
class AccessAttempt:
    """Redacted evidence for one bounded attempt.

    The object intentionally stores status and hashes, not cookies, tokens or
    response bodies.  ``challenge_required`` means the source required user
    interaction; it is never an instruction to solve or evade the challenge.
    """

    path: AccessPath
    outcome: AccessOutcome
    status_code: int | None = None
    final_url: str | None = None
    elapsed_ms: float = 0.0
    content_sha256: str | None = None
    response_bytes: int | None = None
    challenge_required: bool = False
    passive_marker: bool = False
    error_type: str | None = None
    evidence_id: str | None = None

    def __post_init__(self) -> None:
        if self.final_url is not None and not self.path.allows(self.final_url):
            raise ValueError("final URL is outside the access path allowlist")
        if self.elapsed_ms < 0:
            raise ValueError("elapsed_ms must be non-negative")
        if self.response_bytes is not None and self.response_bytes < 0:
            raise ValueError("response_bytes must be non-negative")
        if self.challenge_required and self.outcome is not AccessOutcome.CHALLENGE_ENFORCED:
            raise ValueError("required challenges must be classified explicitly")

    @property
    def blocked(self) -> bool:
        return self.outcome in {
            AccessOutcome.CHALLENGE_ENFORCED,
            AccessOutcome.ACCESS_BLOCKED,
            AccessOutcome.RATE_LIMITED,
            AccessOutcome.TIMEOUT,
            AccessOutcome.TLS_ERROR,
            AccessOutcome.SCHEMA_INVALID,
            AccessOutcome.TRANSPORT_ERROR,
        }

    def to_dict(self) -> dict[str, object]:
        """Serialize only safe, bounded evidence fields."""

        return {
            "provider": self.path.provider,
            "path_kind": self.path.kind.value,
            "url": _safe_url(self.path.url),
            "outcome": self.outcome.value,
            "status_code": self.status_code,
            "final_url": _safe_url(self.final_url) if self.final_url else None,
            "elapsed_ms": self.elapsed_ms,
            "content_sha256": self.content_sha256,
            "response_bytes": self.response_bytes,
            "challenge_required": self.challenge_required,
            "passive_marker": self.passive_marker,
            "error_type": self.error_type,
            "evidence_id": self.evidence_id,
        }


def classify_access(
    *,
    path: AccessPath,
    status_code: int | None,
    headers: Mapping[str, str] | None = None,
    body_marker: str | None = None,
    elapsed_ms: float = 0.0,
    final_url: str | None = None,
    content_sha256: str | None = None,
    response_bytes: int | None = None,
) -> AccessAttempt:
    """Classify a response without treating a challenge as an empty result.

    A marker in a successful response is passive unless the caller explicitly
    tells us that the response prevented the requested operation.  This keeps
    harmless CAPTCHA/WAF scripts from being mistaken for a hard block while
    preserving a real challenge as an explicit outcome.
    """

    normalized_headers = {key.lower(): value.lower() for key, value in (headers or {}).items()}
    marker = (body_marker or "").lower()
    has_marker = any(token in marker for token in ("captcha", "turnstile", "challenge", "waf"))
    if status_code == 429:
        outcome = AccessOutcome.RATE_LIMITED
        challenge = False
    elif status_code in {401, 403}:
        outcome = AccessOutcome.ACCESS_BLOCKED
        challenge = has_marker
    elif status_code is None:
        outcome = AccessOutcome.TRANSPORT_ERROR
        challenge = False
    elif status_code >= 500:
        outcome = AccessOutcome.TRANSPORT_ERROR
        challenge = False
    elif has_marker and _challenge_prevented_operation(normalized_headers, marker):
        outcome = AccessOutcome.CHALLENGE_ENFORCED
        challenge = True
    elif status_code == 200:
        outcome = AccessOutcome.PASSIVE_MARKER if has_marker else AccessOutcome.SUCCESS
        challenge = False
    else:
        outcome = AccessOutcome.SUCCESS
        challenge = False
    return AccessAttempt(
        path=path,
        outcome=outcome,
        status_code=status_code,
        final_url=final_url,
        elapsed_ms=elapsed_ms,
        content_sha256=content_sha256,
        response_bytes=response_bytes,
        challenge_required=challenge,
        passive_marker=has_marker and not challenge,
    )


def _challenge_prevented_operation(headers: Mapping[str, str], marker: str) -> bool:
    return "text/html" in headers.get("content-type", "") and any(
        token in marker for token in ("verify you are human", "access denied", "challenge required")
    )


def _normalize_host(value: str) -> str:
    return value.strip().lower().removeprefix("https://").removeprefix("http://").rstrip(".")


def _safe_url(value: str) -> str:
    parsed = urlparse(value)
    return f"{parsed.scheme}://{parsed.hostname or 'unknown'}{parsed.path}"


__all__ = [
    "AccessAttempt",
    "AccessOutcome",
    "AccessPath",
    "AccessPathKind",
    "classify_access",
]
