"""Opt-in health diagnostics for public jurisprudence providers."""

from __future__ import annotations

import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, cast

from nanojuris.errors import (
    AccessControlRequiredError,
    InternalProviderError,
    NanoJurisError,
    NetworkConfigurationError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
    UnsupportedProviderError,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.base import JurisprudenceProvider


class ProviderHealthStatus(str, Enum):
    """Operational status produced by an explicit provider health check."""

    HEALTHY = "healthy"
    EMPTY = "empty"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    SOURCE_UNAVAILABLE = "source_unavailable"
    SOURCE_CHANGED = "source_changed"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(slots=True)
class ProviderHealthReport:
    """Auditable result of one provider health check."""

    source: str
    status: ProviderHealthStatus
    checked_at: str
    elapsed_ms: float | None = None
    query_text: str = ""
    returned: int = 0
    reported_total: int | None = None
    pagination_mode: str | None = None
    completeness: bool | None = None
    completeness_reason: str | None = None
    source_url: str | None = None
    error_type: str | None = None
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def operational(self) -> bool:
        """Return whether the source answered without an operational error."""

        return self.status in {ProviderHealthStatus.HEALTHY, ProviderHealthStatus.EMPTY}

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["operational"] = self.operational
        return payload


def check_provider(
    provider: JurisprudenceProvider,
    *,
    text: str = "responsabilidade civil",
    page_size: int = 1,
) -> ProviderHealthReport:
    """Run one explicit, small search against a provider."""

    checked_at = _now_iso()
    started = time.perf_counter()
    try:
        page = provider.search(JurisprudenceQuery(text=text, page=1, page_size=page_size))
    except Exception as exc:
        return _error_report(
            source=provider.name,
            checked_at=checked_at,
            started=started,
            query_text=text,
            error=exc,
        )

    return ProviderHealthReport(
        source=provider.name,
        status=(ProviderHealthStatus.HEALTHY if page.results else ProviderHealthStatus.EMPTY),
        checked_at=checked_at,
        elapsed_ms=_elapsed_ms(started),
        query_text=text,
        returned=len(page.results),
        reported_total=page.total,
        pagination_mode=page.pagination_mode,
        completeness=page.is_complete,
        completeness_reason=page.completeness_reason,
        source_url=page.source_trace.source_url if page.source_trace else None,
        details={
            "source_trace": page.source_trace.to_dict() if page.source_trace else None,
        },
    )


def check_sources(
    client: Any,
    *,
    sources: list[str] | None = None,
    text: str = "responsabilidade civil",
    page_size: int = 1,
    timeout: float | None = None,
    max_workers: int | None = None,
) -> dict[str, Any]:
    """Check selected sources concurrently and preserve one report per source."""

    selected = list(sources) if sources is not None else client._default_unified_sources()
    if not selected:
        return {
            "query": {"text": text, "page_size": page_size},
            "checked_sources": [],
            "reports": [],
            "summary": {},
            "complete": True,
        }

    configured_workers = cast(int, getattr(client.config, "unified_max_workers", 6))
    configured_timeout = cast(float, getattr(client.config, "unified_timeout", 60.0))
    workers = int(max_workers or configured_workers)
    deadline = float(timeout or configured_timeout)
    executor = ThreadPoolExecutor(max_workers=max(1, min(workers, len(selected))))
    futures = {
        source: executor.submit(
            _check_source,
            client,
            source,
            text=text,
            page_size=page_size,
        )
        for source in selected
    }
    _done, pending = wait(futures.values(), timeout=deadline)
    reports: dict[str, ProviderHealthReport] = {}
    for source in selected:
        future = futures[source]
        if future in pending:
            reports[source] = _timeout_report(source=source, text=text)
            continue
        reports[source] = future.result()
    executor.shutdown(wait=False, cancel_futures=True)

    ordered = [reports[source] for source in selected]
    counts = Counter(report.status.value for report in ordered)
    return {
        "query": {"text": text, "page_size": page_size},
        "checked_sources": selected,
        "reports": [report.to_dict() for report in ordered],
        "summary": dict(sorted(counts.items())),
        "complete": not pending,
    }


def _check_source(
    client: Any,
    source: str,
    *,
    text: str,
    page_size: int,
) -> ProviderHealthReport:
    provider = client.providers.get(source)
    if provider is None:
        return _error_report(
            source=source,
            checked_at=_now_iso(),
            started=time.perf_counter(),
            query_text=text,
            error=UnsupportedProviderError(f"Unknown provider: {source}"),
        )
    return check_provider(provider, text=text, page_size=page_size)


def _error_report(
    *,
    source: str,
    checked_at: str,
    started: float,
    query_text: str,
    error: Exception,
) -> ProviderHealthReport:
    status = _status_for_error(error)
    return ProviderHealthReport(
        source=source,
        status=status,
        checked_at=checked_at,
        elapsed_ms=_elapsed_ms(started),
        query_text=query_text,
        error_type=type(error).__name__,
        message=str(error),
    )


def _timeout_report(*, source: str, text: str) -> ProviderHealthReport:
    return ProviderHealthReport(
        source=source,
        status=ProviderHealthStatus.TIMEOUT,
        checked_at=_now_iso(),
        query_text=text,
        error_type="TimeoutError",
        message="health check global timeout exceeded",
    )


def _status_for_error(error: Exception) -> ProviderHealthStatus:
    if isinstance(error, AccessControlRequiredError):
        return ProviderHealthStatus.BLOCKED
    if isinstance(error, RateLimitDetectedError):
        return ProviderHealthStatus.RATE_LIMITED
    if isinstance(error, ParserContractChangedError):
        return ProviderHealthStatus.SOURCE_CHANGED
    if isinstance(error, (NetworkConfigurationError, SourceUnavailableError)):
        return ProviderHealthStatus.SOURCE_UNAVAILABLE
    if isinstance(error, (NanoJurisError, InternalProviderError)):
        return ProviderHealthStatus.ERROR
    return ProviderHealthStatus.ERROR


def _now_iso() -> str:
    from nanojuris.models import utc_now_iso

    return utc_now_iso()


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)
