"""Domain exceptions for NanoJuris."""

from __future__ import annotations


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
