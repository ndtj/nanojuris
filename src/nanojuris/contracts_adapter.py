"""Compatibility helpers for adopting the provider contract incrementally.

The adapter is deliberately side-effect free. Existing providers keep their
public return values and exceptions; callers can opt into a typed outcome at a
boundary such as a federated runner, an audit job or an export pipeline.
"""

from __future__ import annotations

import ssl
from collections.abc import Mapping

from nanojuris.contracts import ProviderOutcome, ProviderOutcomeStatus
from nanojuris.errors import (
    AccessControlRequiredError,
    InvalidQueryError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import SearchPage, SourceTrace


def outcome_from_page(page: SearchPage, *, operation: str = "search") -> ProviderOutcome:
    """Wrap a legacy page without changing or copying its result records."""

    return ProviderOutcome.from_page(page, operation=operation)


def outcome_from_error(
    provider: str,
    error: BaseException,
    *,
    operation: str = "search",
    trace: SourceTrace | None = None,
    retryable: bool | None = None,
) -> ProviderOutcome:
    """Map a legacy exception to a safe, typed outcome.

    The mapping is conservative: only known transient failures are marked
    retryable. The original exception is never serialized; only its class and
    redacted message are retained by ``ProviderOutcome``.
    """

    status, default_retryable = classify_error(error)
    return ProviderOutcome(
        provider=provider,
        operation=operation,
        status=status,
        retryable=default_retryable if retryable is None else retryable,
        error_type=type(error).__name__,
        message=str(error),
        trace=trace,
    )


def classify_error(error: BaseException) -> tuple[ProviderOutcomeStatus, bool]:
    """Return a stable status and retry policy for a provider exception."""

    if isinstance(error, AccessControlRequiredError):
        return ProviderOutcomeStatus.BLOCKED, False
    if isinstance(error, RateLimitDetectedError):
        return ProviderOutcomeStatus.RATE_LIMITED, True
    if isinstance(error, ParserContractChangedError):
        return ProviderOutcomeStatus.PARSER_CHANGED, False
    if isinstance(error, InvalidQueryError):
        return ProviderOutcomeStatus.INVALID_QUERY, False
    if isinstance(error, TimeoutError):
        return ProviderOutcomeStatus.TIMEOUT, True
    if isinstance(error, ssl.SSLError):
        return ProviderOutcomeStatus.TLS_ERROR, True
    if isinstance(error, SourceUnavailableError):
        return ProviderOutcomeStatus.UNAVAILABLE, True
    if isinstance(error, ConnectionError):
        return ProviderOutcomeStatus.UNAVAILABLE, True
    return ProviderOutcomeStatus.UNAVAILABLE, False


def normalize_filters_applied(filters: Mapping[str, object]) -> dict[str, str]:
    """Serialize applied-filter metadata deterministically at an API edge."""

    return {str(name): str(value) for name, value in sorted(filters.items())}


__all__ = [
    "classify_error",
    "normalize_filters_applied",
    "outcome_from_error",
    "outcome_from_page",
]
