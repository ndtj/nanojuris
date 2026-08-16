"""Opt-in live contract validation for public jurisprudence providers."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, cast

from nanojuris.errors import (
    AccessControlRequiredError,
    InternalProviderError,
    NanoJurisError,
    NetworkConfigurationError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
    UnsupportedProviderError,
    UnsupportedQueryError,
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
    NETWORK_CONFIGURATION = "network_configuration"
    TLS_VERIFICATION_FAILED = "tls_verification_failed"
    ERROR = "error"
    QUERY_REJECTED = "query_rejected"
    UNSUPPORTED_QUERY = "unsupported_query"


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
    endpoint: str | None = None
    http_status: int | None = None
    access_status: str | None = None
    retrieval_status: str | None = None
    extraction_status: str | None = None
    requested_page_size: int | None = None
    effective_page_size: int | None = None
    content_type: str | None = None
    content_sha256: str | None = None
    response_bytes: int | None = None
    full_text_status: str | None = None
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
            "page_size": page.page_size >= page_size,
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
    trace = page.source_trace
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
        endpoint=trace.endpoint if trace else None,
        http_status=trace.http_status if trace else None,
        access_status=_aggregate_result_status(page.results, "access_status"),
        retrieval_status=trace.retrieval_status if trace else None,
        extraction_status=_aggregate_result_status(page.results, "extraction_status"),
        requested_page_size=page_size,
        effective_page_size=page.page_size,
        content_type=trace.content_type if trace else None,
        content_sha256=trace.content_sha256 if trace else None,
        response_bytes=trace.response_bytes if trace else None,
        full_text_status=_full_text_status(page.results),
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
        "schema_version": "1.0",
        "query": {
            "text": text,
            "sha256": _query_hash(text=text, page_size=page_size),
            "page_size": page_size,
        },
        "checked_sources": selected,
        "reports": [report.to_dict() for report in ordered],
        "summary": dict(sorted(counts.items())),
        "complete": not pending,
        "passed": not pending and all(report.passed for report in ordered),
    }


def write_validation_artifacts(
    payload: dict[str, Any],
    *,
    output_dir: Path | str,
    scope: str = "provider-validation",
) -> tuple[Path, Path]:
    """Persist one validation run as machine-readable JSON and concise Markdown.

    The caller controls the output directory so library use never writes to a
    project checkout implicitly. Files are deterministic for a given payload
    except for the run timestamp, which comes from the validation reports.
    """

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    reports = payload.get("reports", [])
    checked_at = next(
        (
            str(report.get("checked_at"))
            for report in reports
            if isinstance(report, dict) and report.get("checked_at")
        ),
        _now_iso(),
    )
    timestamp = checked_at.replace("+00:00", "Z").replace(":", "").replace("-", "")
    safe_scope = "".join(
        character if character.isalnum() or character in {"-", "_"} else "-" for character in scope
    )
    stem = f"{timestamp}-{safe_scope.strip('-') or 'provider-validation'}"
    json_path = directory / f"{stem}.json"
    markdown_path = directory / f"{stem}.md"
    artifact = {
        "schema_version": "1.0",
        "scope": scope,
        "generated_at": _now_iso(),
        **payload,
    }
    json_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_validation_markdown(artifact), encoding="utf-8")
    return json_path, markdown_path


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
        requested_page_size=1,
        error_type=type(error).__name__,
        message=str(error),
    )


def _status_for_error(error: Exception) -> ProviderValidationStatus:
    error_text = " | ".join(str(item) for item in _exception_chain(error)).lower()
    if "proxyerror" in error_text or "unable to connect to proxy" in error_text:
        return ProviderValidationStatus.NETWORK_CONFIGURATION
    if "ssl" in error_text and ("certificate" in error_text or "certificado" in error_text):
        return ProviderValidationStatus.TLS_VERIFICATION_FAILED
    if isinstance(error, AccessControlRequiredError):
        return ProviderValidationStatus.BLOCKED
    if isinstance(error, RateLimitDetectedError):
        return ProviderValidationStatus.RATE_LIMITED
    if isinstance(error, ParserContractChangedError):
        return ProviderValidationStatus.SOURCE_CHANGED
    if isinstance(error, QueryRejectedError):
        return ProviderValidationStatus.QUERY_REJECTED
    if isinstance(error, UnsupportedQueryError):
        return ProviderValidationStatus.UNSUPPORTED_QUERY
    if isinstance(error, (NetworkConfigurationError, SourceUnavailableError)):
        return ProviderValidationStatus.SOURCE_UNAVAILABLE
    if isinstance(error, (NanoJurisError, InternalProviderError)):
        return ProviderValidationStatus.ERROR
    return ProviderValidationStatus.ERROR


def _exception_chain(error: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        chain.append(current)
        seen.add(id(current))
        current = current.__cause__ or current.__context__
    return chain


def _has_legal_content(result: Any) -> bool:
    return any(
        bool(str(value).strip())
        for value in (result.summary, result.thesis, result.question, result.full_text)
    )


def _aggregate_result_status(results: list[Any], field_name: str) -> str | None:
    """Return one truthful status value without inventing a public default."""

    values = {
        getattr(getattr(result, field_name, None), "value", getattr(result, field_name, None))
        for result in results
        if getattr(result, field_name, None) is not None
    }
    if not values:
        return None
    if len(values) == 1:
        return str(next(iter(values)))
    return "mixed"


def _full_text_status(results: list[Any]) -> str:
    if not results:
        return "not_returned"
    if all(bool(getattr(result, "full_text", None)) for result in results):
        return "returned"
    if any(bool((getattr(result, "raw", None) or {}).get("document_url")) for result in results):
        return "document_available"
    return "not_returned"


def _query_hash(*, text: str, page_size: int) -> str:
    normalized = json.dumps(
        {"text": text, "page_size": page_size}, ensure_ascii=False, sort_keys=True
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _render_validation_markdown(artifact: dict[str, Any]) -> str:
    query = artifact.get("query", {})
    reports = artifact.get("reports", [])
    lines = [
        f"# Validação Live — {artifact.get('scope', 'provider-validation')}",
        "",
        "Artefato gerado pelo NanoJuris. Esta execução registra observações de uma janela",
        "limitada; não representa garantia permanente de disponibilidade da fonte.",
        "",
        f"- Gerado em: `{artifact.get('generated_at')}`",
        f"- Consulta: `{query.get('text', '')}`",
        f"- Hash da consulta: `{query.get('sha256', '')}`",
        f"- Tamanho solicitado: `{query.get('page_size', '')}`",
        "",
        (
            "| Fonte | Estado | Retornados | Total remoto | Acesso | Extração | "
            "Paginação | Latência | Evidência |"
        ),
        "| --- | --- | ---: | ---: | --- | --- | --- | ---: | --- |",
    ]
    for report in reports:
        if not isinstance(report, dict):
            continue
        lines.append(
            "| `{source}` | `{status}` | {returned} | {total} | `{access}` | `{extraction}` | "
            "`{pagination}` | {elapsed} ms | {evidence} |".format(
                source=report.get("source", ""),
                status=report.get("status", ""),
                returned=report.get("returned", 0),
                total=report.get("reported_total")
                if report.get("reported_total") is not None
                else "-",
                access=report.get("access_status") or "not_observed",
                extraction=report.get("extraction_status") or "not_observed",
                pagination=report.get("pagination_mode") or "unknown",
                elapsed=report.get("elapsed_ms") if report.get("elapsed_ms") is not None else "-",
                evidence=report.get("endpoint")
                or report.get("error_type")
                or "normalized response",
            )
        )
    lines.extend(
        [
            "",
            "## Limitações",
            "",
            "Estados de bloqueio, indisponibilidade, rate limit e mudança de contrato são",
            "registrados como tais e não equivalem a resultado vazio.",
        ]
    )
    return "\n".join(lines) + "\n"


def _now_iso() -> str:
    from nanojuris.models import utc_now_iso

    return utc_now_iso()


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)
