"""Serializable contracts for provider discovery runs."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from nanojuris.models import AccessStatus, ExtractionStatus, ExtractionTrace, SourceTrace


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class DiscoveryStatus(str, Enum):
    """Operational status of an observed route."""

    VALID = "valid"
    CANDIDATE = "candidate"
    EMPTY = "empty"
    INVALID_QUERY = "invalid_query"
    ACCESS_CONTROLLED = "access_controlled"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    SOURCE_UNAVAILABLE = "source_unavailable"
    REDIRECT_OUTSIDE_ALLOWLIST = "redirect_outside_allowlist"
    TLS_ERROR = "tls_error"
    ROBOTS_DISALLOWED = "robots_disallowed"
    PARSER_CHANGED = "parser_changed"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class DiscoveryPolicy:
    """Explicit limits for a local discovery run."""

    allowed_domains: tuple[str, ...]
    max_pages: int = 20
    max_depth: int = 2
    max_bytes_per_response: int = 5_000_000
    max_total_bytes: int = 25_000_000
    max_redirects: int = 5
    max_browser_responses: int = 100
    timeout_seconds: float = 30.0
    delay_seconds: float = 0.25
    respect_robots: bool = True
    user_agent: str = "NanoJuris/provider-discovery"

    def __post_init__(self) -> None:
        domains = tuple(
            domain.lower().strip().rstrip(".") for domain in self.allowed_domains if domain.strip()
        )
        if not domains:
            raise ValueError("allowed_domains deve conter ao menos um domínio")
        if any("/" in domain or ":" in domain for domain in domains):
            raise ValueError("allowed_domains deve conter apenas hostnames")
        if self.max_pages < 1 or self.max_depth < 0:
            raise ValueError("max_pages deve ser positivo e max_depth não pode ser negativo")
        if self.max_bytes_per_response < 1 or self.max_total_bytes < self.max_bytes_per_response:
            raise ValueError("limites de bytes inválidos")
        if self.max_redirects < 0 or self.max_browser_responses < 1:
            raise ValueError("limites de redirects/respostas inválidos")
        if self.timeout_seconds <= 0 or self.delay_seconds < 0:
            raise ValueError("timeout/delay inválidos")
        object.__setattr__(self, "allowed_domains", domains)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DiscoveryRequest:
    """Request observed or issued by the discovery worker."""

    method: str
    url: str
    query: dict[str, Any] = field(default_factory=dict)
    body: Any | None = None
    headers: dict[str, str] = field(default_factory=dict)

    def to_dict(self, *, redacted: bool = False) -> dict[str, Any]:
        from nanojuris.discovery.policy import redact_mapping, redact_value

        return {
            "method": self.method.upper(),
            "url": redact_value(self.url) if redacted else self.url,
            "query": redact_mapping(self.query) if redacted else self.query,
            "body": redact_value(self.body) if redacted else self.body,
            "headers": redact_mapping(self.headers) if redacted else self.headers,
        }


@dataclass(slots=True)
class DiscoveryResponse:
    """Bounded response payload with reproducibility metadata."""

    status_code: int | None
    url: str
    final_url: str | None = None
    content_type: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = field(default=b"", repr=False, compare=False)
    elapsed_ms: float | None = None
    redirects: list[dict[str, Any]] = field(default_factory=list)
    transport_status: str = "complete"
    error_type: str | None = None
    error: str | None = None

    @property
    def content_sha256(self) -> str:
        return hashlib.sha256(self.body).hexdigest()

    @property
    def response_bytes(self) -> int:
        return len(self.body)

    def to_dict(self, *, include_body: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status_code": self.status_code,
            "url": self.url,
            "final_url": self.final_url,
            "content_type": self.content_type,
            "headers": self.headers,
            "response_bytes": self.response_bytes,
            "content_sha256": self.content_sha256,
            "elapsed_ms": self.elapsed_ms,
            "redirects": self.redirects,
            "transport_status": self.transport_status,
            "error_type": self.error_type,
            "error": self.error,
        }
        if include_body:
            payload["body_base64"] = base64.b64encode(self.body).decode("ascii")
        return payload


@dataclass(slots=True)
class RouteCandidate:
    """A route discovered from a document, form or browser event."""

    url: str
    method: str = "GET"
    source: str = "document"
    reason: str = ""
    content_type: str = ""
    confidence: float = 0.0
    depth: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SelectorCandidate:
    """A reviewable, non-authoritative field selector suggestion."""

    field: str
    selector: str
    label: str
    matches: int
    confidence: float
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FilterCandidate:
    """A reviewable input/filter observed in a public response."""

    name: str
    field_type: str = "unknown"
    label: str = ""
    values: list[str] = field(default_factory=list)
    required: bool = False
    source: str = "document"
    confidence: float = 0.0
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DiscoveryEvidence:
    """One auditable observation produced by HTTP or browser discovery."""

    run_id: str
    captured_at: str
    seed_url: str
    request: DiscoveryRequest
    response: DiscoveryResponse
    status: DiscoveryStatus
    access_status: AccessStatus = AccessStatus.PARTIAL
    extraction_status: ExtractionStatus = ExtractionStatus.PARTIAL
    route_candidates: list[RouteCandidate] = field(default_factory=list)
    selector_candidates: list[SelectorCandidate] = field(default_factory=list)
    filter_candidates: list[FilterCandidate] = field(default_factory=list)
    access_signals: dict[str, bool] = field(default_factory=dict)
    legal_signals: dict[str, bool] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    source: str = "http"

    def to_dict(self, *, include_body: bool = False) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "captured_at": self.captured_at,
            "seed_url": self.seed_url,
            "request": self.request.to_dict(redacted=True),
            "response": self.response.to_dict(include_body=include_body),
            "status": self.status.value,
            "access_status": self.access_status.value,
            "extraction_status": self.extraction_status.value,
            "route_candidates": [candidate.to_dict() for candidate in self.route_candidates],
            "selector_candidates": [candidate.to_dict() for candidate in self.selector_candidates],
            "filter_candidates": [candidate.to_dict() for candidate in self.filter_candidates],
            "access_signals": self.access_signals,
            "legal_signals": self.legal_signals,
            "limitations": self.limitations,
            "source": self.source,
        }

    def to_traces(self, provider: str) -> tuple[SourceTrace, ExtractionTrace]:
        source_trace = SourceTrace(
            provider=provider,
            endpoint=self.request.url,
            query=self.request.query,
            source_url=self.seed_url,
            limitations=list(self.limitations),
            http_status=self.response.status_code,
            final_url=self.response.final_url,
            content_type=self.response.content_type,
            content_sha256=self.response.content_sha256,
            response_bytes=self.response.response_bytes,
            elapsed_ms=self.response.elapsed_ms,
            retrieval_status=self.status.value,
            transformations=["discovery-bounded", f"source:{self.source}"],
        )
        extraction_trace = ExtractionTrace(
            parser="nanojuris.discovery",
            parser_version="0.1.0",
            status=self.extraction_status,
            access_status=self.access_status,
            content_sha256=self.response.content_sha256,
            content_bytes=self.response.response_bytes,
            warnings=list(self.limitations),
            transformations=["route-candidate-extraction"],
            metadata={"discovery_status": self.status.value},
        )
        return source_trace, extraction_trace


@dataclass(slots=True)
class DiscoveryRun:
    """Collection of bounded observations and run-level metrics."""

    run_id: str
    started_at: str
    policy: DiscoveryPolicy
    evidences: list[DiscoveryEvidence] = field(default_factory=list)
    finished_at: str | None = None

    def to_dict(self, *, include_body: bool = False) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "policy": self.policy.to_dict(),
            "evidences": [
                evidence.to_dict(include_body=include_body) for evidence in self.evidences
            ],
            "metrics": self.metrics(),
        }

    def metrics(self) -> dict[str, Any]:
        return {
            "observations": len(self.evidences),
            "response_bytes": sum(evidence.response.response_bytes for evidence in self.evidences),
            "statuses": _count_values(evidence.status.value for evidence in self.evidences),
            "access_statuses": _count_values(
                evidence.access_status.value for evidence in self.evidences
            ),
            "route_candidates": sum(len(evidence.route_candidates) for evidence in self.evidences),
            "selector_candidates": sum(
                len(evidence.selector_candidates) for evidence in self.evidences
            ),
            "filter_candidates": sum(
                len(evidence.filter_candidates) for evidence in self.evidences
            ),
        }


def _count_values(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts
