"""Domain exceptions for NanoJuris."""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

MAX_PUBLIC_ERROR_MESSAGE_LENGTH = 500

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_BEARER_RE = re.compile(r"\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?:authorization|proxy-authorization|api[_-]?key|x-api-key|"
    r"access[_-]?token|refresh[_-]?token|id[_-]?token|client[_-]?secret|"
    r"password|passwd|secret|credential)\b\s*[:=]\s*[^,;\s]+"
)
_SECRET_JSON_RE = re.compile(
    r"(?i)([\"']?(?:authorization|proxy-authorization|api[_-]?key|x-api-key|"
    r"access[_-]?token|refresh[_-]?token|id[_-]?token|client[_-]?secret|"
    r"password|passwd|secret|credential)[\"']?\s*:\s*)"
    r"([\"']?)(?:[^\"',}\s]+)\2"
)
_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


def safe_error_message(
    error: BaseException | str,
    *,
    limit: int = MAX_PUBLIC_ERROR_MESSAGE_LENGTH,
) -> str:
    """Return a bounded diagnostic safe for public provider payloads.

    Provider exceptions frequently include a request URL, headers or a remote
    response body. Those details are useful while debugging locally but must
    not be copied into API responses, traces or persisted research metadata.
    This helper intentionally keeps the error class separate from its message;
    callers can retain ``type(error).__name__`` without exposing the payload.
    """

    if limit < 1:
        raise ValueError("limit must be positive")
    message = str(error).replace("\r", " ").replace("\n", " ")
    message = _URL_RE.sub(_safe_url, message)
    message = _BEARER_RE.sub(r"\1 [REDACTED]", message)
    message = _SECRET_ASSIGNMENT_RE.sub(
        lambda match: f"{match.group(0).split(':', 1)[0].split('=', 1)[0].rstrip()}=[REDACTED]",
        message,
    )
    message = _SECRET_JSON_RE.sub(r"\1[REDACTED]", message)
    message = _EMAIL_RE.sub("[REDACTED_EMAIL]", message)
    message = re.sub(r"\s+", " ", message).strip()
    if not message:
        message = type(error).__name__ if isinstance(error, BaseException) else "provider error"
    if len(message) > limit:
        message = message[: max(0, limit - 14)].rstrip() + "...[truncated]"
    return message


def _safe_url(match: re.Match[str]) -> str:
    """Keep a provider origin/path while dropping query, fragment and auth."""

    value = match.group(0).rstrip(".,);]}")
    trailing = match.group(0)[len(value) :]
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname or "unknown-host"
        port = f":{parsed.port}" if parsed.port is not None else ""
        safe = urlunsplit((parsed.scheme, hostname + port, parsed.path, "", ""))
        return safe + trailing
    except ValueError:
        return "[REDACTED_URL]" + trailing


class NanoJurisError(Exception):
    """Base exception for all NanoJuris errors."""


class SourceUnavailableError(NanoJurisError):
    """Raised when a public source is unavailable or returns an invalid response."""


class NetworkConfigurationError(SourceUnavailableError):
    """Raised when local network or proxy configuration blocks a public source."""


class AccessControlRequiredError(NanoJurisError):
    """Raised when a source requires login, captcha or another access control."""


class RateLimitDetectedError(NanoJurisError):
    """Raised when a source signals throttling or excessive usage."""


class ParserContractChangedError(NanoJurisError):
    """Raised when a source response no longer matches the expected contract."""


class UnsupportedProviderError(NanoJurisError):
    """Raised when a provider name is unknown."""


class InvalidQueryError(NanoJurisError):
    """Raised when a public query is invalid or contains unknown filters."""


class QueryRejectedError(InvalidQueryError):
    """Raised when a source rejects an otherwise well-formed query payload."""


class UnsupportedQueryError(NanoJurisError):
    """Raised when a valid query uses an operation a source cannot guarantee."""


class InternalProviderError(NanoJurisError):
    """Raised when a provider fails because of an unexpected programming error."""
