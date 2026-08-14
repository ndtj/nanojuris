"""Opt-in live contract validation for public jurisprudence providers."""

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


class ProviderValidationStatus(str, Enum):
    """Result of a live provider contract validation."""

    VALID = "valid"
    EMPTY = "empty"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    SOURCE_UNAVAILABLE = "source_unavailable"
    SOURCE_CHANGED = "source_changed"
    CONTRACT_INVALID = "contract_invalid"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(slots=True)
class ProviderValidationReport:
    """Auditable report for one live provider contract check."""

    source: str
    status: ProviderValidationStatus
    checked_at: str
    elapsed_ms: float | None = None
    query_text: str = ""
    returned: int = 0
    reported_total: int | None = None
    pagination_mode: str | None = None
    completeness: bool | None = None
    completeness_reason: str | None = None
    source_url: str | None = None
    checks: dict[str, bool] = field(default_factory=dict)
    failed_checks: list[str] = field(default_factory=list)
    error_type: str | None = None
    message: str | None = None

    @property
    def passed(self) -> bool:
        """Return whether the provider met the minimum live contract."""

        return self.status in {ProviderValidationStatus.VALID, ProviderValidationStatus.EMPTY}

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["passed"] = self.passed
        return payload


def validate_provider(
    provider: JurisprudenceProvider,
    *,
    text: str = "responsabilidade civil",
    page_size: int = 1,
) -> ProviderValidationReport:
    """Run one small live query and validate its normalized response contract."""

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

    try:
        checks = {
            "page_source": page.source == provider.name,
            "page_trace": page.source_trace is not None,
            "page_number": page.page == 1,
            "page_size": page.page_size == page_size,
            "reported_total_nonnegative": page.total >= 0,
        }
        if page.results:
            checks.update(
                {
                    "result_ids": all(bool(str(item.id or "").strip()) for item in page.results),
                    "result_sources": all(item.source == provider.name for item in page.results),
                    "result_content": all(_has_legal_content(item) for item in page.results),
                    "result_traces": all(item.source_trace is not None for item in page.results),
                }
            )
    except Exception as exc:
        return ProviderValidationReport(
            source=provider.name,
            status=ProviderValidationStatus.CONTRACT_INVALID,
            checked_at=checked_at,
            elapsed_ms=_elapsed_ms(started),
            query_text=text,
            failed_checks=["normalized_response"],
            error_type=type(exc).__name__,
            message=f"normalized provider response could not be validated: {exc}",
        )
    failed_checks = [name for name, passed in checks.items() if not passed]
    if failed_checks:
        status = ProviderValidationStatus.CONTRACT_INVALID
    else:
        status = ProviderValidationStatus.VALID if page.results else ProviderValidationStatus.EMPTY
    return ProviderValidationReport(
        source=provider.name,
        status=status,
        checked_at=checked_at,
        elapsed_ms=_elapsed_ms(started),
        query_text=text,
        returned=len(page.results),
        reported_total=page.total,
        pagination_mode=page.pagination_mode,
        completeness=page.is_complete,
        completeness_reason=page.completeness_reason,
        source_url=page.source_trace.source_url if page.source_trace else None,
        checks=checks,
        failed_checks=failed_checks,
    )


def validate_sources(
    client: Any,
    *,
    sources: list[str] | None = None,
    text: str = "responsabilidade civil",
    page_size: int = 1,
    timeout: float | None = None,
    max_workers: int | None = None,
) -> dict[str, Any]:
    """Validate selected sources concurrently and preserve source order."""

    selected = list(sources) if sources is not None else client._default_unified_sources()
    if not selected:
        return {
            "query": {"text": text, "page_size": page_size},
            "checked_sources": [],
            "reports": [],
            "summary": {},
            "complete": True,
            "passed": True,
        }

    configured_workers = cast(Any, max_workers)
    if configured_workers is None:
        configured_workers = getattr(client.config, "unified_max_workers", 6)
    configured_timeout = cast(Any, timeout)
    if configured_timeout is None:
        configured_timeout = getattr(client.config, "unified_timeout", 60.0)
    workers = int(configured_workers)
    deadline = float(configured_timeout)
    executor = ThreadPoolExecutor(max_workers=max(1, min(workers, len(selected))))
    futures = {
        source: executor.submit(
            _validate_source,
            client,
            source,
            text=text,
            page_size=page_size,
        )
        for source in selected
    }
    _done, pending = wait(futures.values(), timeout=deadline)
    reports: dict[str, ProviderValidationReport] = {}
    for source in selected:
        future = futures[source]
        if future in pending:
            reports[source] = ProviderValidationReport(
                source=source,
                status=ProviderValidationStatus.TIMEOUT,
                checked_at=_now_iso(),
                query_text=text,
                error_type="TimeoutError",
                message="validation global timeout exceeded",
            )
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
        "passed": not pending and all(report.passed for report in ordered),
    }


def _validate_source(
    client: Any,
    source: str,
    *,
    text: str,
    page_size: int,
) -> ProviderValidationReport:
    provider = client.providers.get(source)
    if provider is None:
        return _error_report(
            source=source,
            checked_at=_now_iso(),
            started=time.perf_counter(),
            query_text=text,
            error=UnsupportedProviderError(f"Unknown provider: {source}"),
        )
    return validate_provider(provider, text=text, page_size=page_size)


def _error_report(
    *,
    source: str,
    checked_at: str,
    started: float,
    query_text: str,
    error: Exception,
) -> ProviderValidationReport:
    return ProviderValidationReport(
        source=source,
        status=_status_for_error(error),
        checked_at=checked_at,
        elapsed_ms=_elapsed_ms(started),
        query_text=query_text,
        error_type=type(error).__name__,
        message=str(error),
    )


def _status_for_error(error: Exception) -> ProviderValidationStatus:
    if isinstance(error, AccessControlRequiredError):
        return ProviderValidationStatus.BLOCKED
    if isinstance(error, RateLimitDetectedError):
        return ProviderValidationStatus.RATE_LIMITED
    if isinstance(error, ParserContractChangedError):
        return ProviderValidationStatus.SOURCE_CHANGED
    if isinstance(error, (NetworkConfigurationError, SourceUnavailableError)):
        return ProviderValidationStatus.SOURCE_UNAVAILABLE
    if isinstance(error, (NanoJurisError, InternalProviderError)):
        return ProviderValidationStatus.ERROR
    return ProviderValidationStatus.ERROR


def _has_legal_content(result: Any) -> bool:
    return any(
        bool(str(value).strip())
        for value in (result.summary, result.thesis, result.question, result.full_text)
    )


def _now_iso() -> str:
    from nanojuris.models import utc_now_iso

    return utc_now_iso()


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)
