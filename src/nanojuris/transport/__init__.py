"""Shared, bounded HTTP runtime for public jurisprudence providers.

The transport layer is deliberately independent from provider parsers.  It
enforces URL allowlists, redirect validation, response-size limits, retry
semantics, per-host rate budgets and safe response metadata while preserving
the raw bytes for the caller.
"""

from nanojuris.transport.cache import ContentResponseCache
from nanojuris.transport.circuit import CircuitBreaker, CircuitState
from nanojuris.transport.client import SharedHttpClient
from nanojuris.transport.models import (
    TransportPolicy,
    TransportRequest,
    TransportResponse,
    TransportStatus,
)
from nanojuris.transport.redaction import redact_headers, redact_payload, redact_url

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "ContentResponseCache",
    "SharedHttpClient",
    "TransportPolicy",
    "TransportRequest",
    "TransportResponse",
    "TransportStatus",
    "redact_headers",
    "redact_payload",
    "redact_url",
]
