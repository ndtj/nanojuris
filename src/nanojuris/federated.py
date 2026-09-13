"""Deterministic planning primitives for federated jurisprudence search.

This module is intentionally an opt-in foundation. It does not call a source
or change ``NanoJurisClient``; it makes filter translation, omitted filters and
continuation state inspectable before an adapter is invoked.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import urlsplit

from nanojuris.contracts import (
    CanonicalFilterRegistry,
    FilterSupport,
    ProviderOutcome,
    ProviderOutcomeStatus,
)
from nanojuris.identity import canonical_record_identity, resolve_legal_identity
from nanojuris.models import (
    CanonicalDecision,
    CanonicalDocument,
    CanonicalPrecedent,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
)
from nanojuris.normalization import normalize_date_value

CURSOR_VERSION = 1


@dataclass(frozen=True, slots=True)
class SearchIntent:
    """User intent independent from one provider's query vocabulary."""

    text: str = ""
    filters: dict[str, Any] = field(default_factory=dict)
    sources: tuple[str, ...] = ()
    ordering: str = "relevance"

    def fingerprint(self) -> str:
        """Return a stable digest used to bind a cursor to its query."""

        payload = {
            "text": self.text,
            "filters": self.filters,
            "sources": list(self.sources),
            "ordering": self.ordering,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ProviderQueryPlan:
    """A source-specific plan with no hidden filter invention."""

    source: str
    provider_query: dict[str, Any]
    filter_support: dict[str, FilterSupport]
    local_filters: dict[str, Any] = field(default_factory=dict)
    omitted_filters: tuple[str, ...] = ()
    transformations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "provider_query": self.provider_query,
            "filter_support": {name: status.value for name, status in self.filter_support.items()},
            "local_filters": self.local_filters,
            "omitted_filters": list(self.omitted_filters),
            "transformations": list(self.transformations),
        }


@dataclass(frozen=True, slots=True)
class FederatedSearchPage:
    """Deterministic merged page with explicit per-source completeness."""

    results: tuple[Any, ...]
    raw_result_count: int
    duplicate_count: int
    source_outcomes: dict[str, ProviderOutcome]
    pages_fetched: dict[str, int]
    complete: bool
    completeness_reason: str | None
    ordering: str
    max_results: int
    provider_plans: dict[str, ProviderQueryPlan] = field(default_factory=dict)
    duplicate_groups: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.raw_result_count < 0 or self.duplicate_count < 0:
            raise ValueError("federated result counts must be non-negative")
        if self.duplicate_count > self.raw_result_count:
            raise ValueError("duplicate_count cannot exceed raw_result_count")
        if self.max_results < 1 or len(self.results) > self.max_results:
            raise ValueError("federated result page exceeds max_results")
        if any(value < 0 for value in self.pages_fetched.values()):
            raise ValueError("pages_fetched must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": [
                result.to_dict() if hasattr(result, "to_dict") else result
                for result in self.results
            ],
            "raw_result_count": self.raw_result_count,
            "duplicate_count": self.duplicate_count,
            "source_outcomes": {
                source: outcome.to_dict() for source, outcome in self.source_outcomes.items()
            },
            "pages_fetched": dict(self.pages_fetched),
            "complete": self.complete,
            "completeness_reason": self.completeness_reason,
            "ordering": self.ordering,
            "max_results": self.max_results,
            "provider_plans": {
                source: plan.to_dict() for source, plan in self.provider_plans.items()
            },
            "duplicate_groups": {
                key: list(sources) for key, sources in self.duplicate_groups.items()
            },
        }


@dataclass(frozen=True, slots=True)
class FederatedCursor:
    """Opaque, versioned continuation positions bound to one intent."""

    query_fingerprint: str
    source_positions: dict[str, str | int] = field(default_factory=dict)
    version: int = CURSOR_VERSION

    def encode(self) -> str:
        payload = {
            "version": self.version,
            "query_fingerprint": self.query_fingerprint,
            "source_positions": self.source_positions,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    @classmethod
    def decode(cls, token: str) -> FederatedCursor:
        if not token or len(token) > 4096:
            raise ValueError("invalid federated cursor")
        padded = token + ("=" * (-len(token) % 4))
        try:
            payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise ValueError("invalid federated cursor") from exc
        if not isinstance(payload, dict) or payload.get("version") != CURSOR_VERSION:
            raise ValueError("unsupported federated cursor version")
        fingerprint = payload.get("query_fingerprint")
        positions = payload.get("source_positions")
        if not isinstance(fingerprint, str) or len(fingerprint) != 64:
            raise ValueError("invalid federated cursor fingerprint")
        if not isinstance(positions, dict) or any(
            not isinstance(name, str) or not isinstance(value, (str, int))
            for name, value in positions.items()
        ):
            raise ValueError("invalid federated cursor positions")
        return cls(
            query_fingerprint=fingerprint,
            source_positions={str(name): value for name, value in positions.items()},
        )

    def matches(self, intent: SearchIntent) -> bool:
        return self.query_fingerprint == intent.fingerprint()


def plan_federated_query(
    intent: SearchIntent,
    capabilities: dict[str, ProviderCapabilities],
) -> list[ProviderQueryPlan]:
    """Build deterministic plans, omitting filters without source evidence."""

    sources = intent.sources or tuple(sorted(capabilities))
    registry = CanonicalFilterRegistry.default()
    plans: list[ProviderQueryPlan] = []
    for source in dict.fromkeys(sources):
        capability = capabilities.get(source)
        provider_query: dict[str, Any] = {"text": intent.text}
        support: dict[str, FilterSupport] = {}
        local_filters: dict[str, Any] = {}
        omitted: list[str] = []
        transformations: list[str] = []
        for raw_name, value in sorted(intent.filters.items()):
            raw_status = _filter_support(capability, raw_name)
            canonical_name = registry.canonicalize(raw_name) or raw_name
            # Preserve an explicitly declared provider alias for backwards
            # compatibility.  Canonicalization is used only when the alias is
            # not declared and the canonical name has evidence.
            name = raw_name if raw_status is not FilterSupport.UNVERIFIED else canonical_name
            if name != raw_name:
                transformations.append(f"canonicalized:{raw_name}->{name}")
            status = _filter_support(capability, name)
            support[name] = status
            if status in {FilterSupport.NATIVE, FilterSupport.TRANSLATED}:
                provider_name = name
                if status is FilterSupport.TRANSLATED:
                    # ProviderCapabilities records the evidence class, not an
                    # alias. A concrete alias must be supplied by a provider
                    # adapter; never invent one in the generic planner.
                    transformations.append(f"translated:{name}")
                provider_query[provider_name] = value
            elif status is FilterSupport.VALIDATED_SCOPE:
                # Scope dimensions (authority/branch/degree/instance/
                # collection) can be enforced by the adapter before the
                # request even when the remote endpoint has no parameter.
                # Keep them visible without pretending they were sent.
                transformations.append(f"validated_scope:{name}")
            elif status is FilterSupport.LOCAL_POSTFILTER:
                local_filters[name] = value
                transformations.append(f"local_postfilter:{name}")
            else:
                omitted.append(name)
        plans.append(
            ProviderQueryPlan(
                source=source,
                provider_query=provider_query,
                filter_support=support,
                local_filters=local_filters,
                omitted_filters=tuple(omitted),
                transformations=tuple(transformations),
            )
        )
    return plans


def merge_federated_pages(
    pages: Mapping[str, Iterable[SearchPage]],
    *,
    outcomes: Mapping[str, ProviderOutcome] | None = None,
    ordering: str = "published_desc",
    max_results: int = 100,
    plans: Mapping[str, ProviderQueryPlan] | None = None,
) -> FederatedSearchPage:
    """Merge bounded provider pages without comparing native relevance scores.

    The merge is intentionally conservative: records are deduplicated only
    when the identity 0037 resolver returns the same stable key.  Unknown
    identities are retained as distinct rows.  A partial/failed source, or a
    result cap, keeps the global page incomplete and exposes the reason.
    """

    if max_results < 1:
        raise ValueError("max_results must be positive")
    if ordering not in {
        "published_desc",
        "published_asc",
        "updated_desc",
        "updated_asc",
        "source_id",
    }:
        raise ValueError(
            "ordering must be published_desc, published_asc, updated_desc, updated_asc or source_id"
        )

    source_pages: dict[str, tuple[SearchPage, ...]] = {}
    rows: list[tuple[str, int, int, Any, str | None]] = []
    for source, iterable in pages.items():
        source_name = str(source)
        materialized = tuple(iterable)
        source_pages[source_name] = materialized
        for page_index, page in enumerate(materialized):
            if page.source != source_name:
                raise ValueError(
                    f"source key {source_name!r} diverges from page source {page.source!r}"
                )
            for record_index, record in enumerate(page.results):
                rows.append(
                    (
                        source_name,
                        page.page,
                        page_index * max(1, page.page_size) + record_index,
                        record,
                        _record_identity_key(record),
                    )
                )

    rows.sort(key=lambda row: _merge_sort_key(row, ordering))
    unique: list[Any] = []
    seen: set[str] = set()
    group_sources: dict[str, set[str]] = {}
    duplicate_count = 0
    for source, page_number, record_index, record, identity_key in rows:
        # A missing identity is deliberately unique.  The row coordinates are
        # deterministic within the supplied pages and avoid false merges.
        dedup_key = (
            f"identity:{identity_key}"
            if identity_key is not None
            else f"row:{source}:{page_number}:{record_index}"
        )
        group_sources.setdefault(dedup_key, set()).add(source)
        if dedup_key in seen:
            duplicate_count += 1
            continue
        seen.add(dedup_key)
        unique.append(record)

    truncated = len(unique) > max_results
    selected = tuple(unique[:max_results])
    duplicate_groups = {
        key: tuple(sorted(sources)) for key, sources in group_sources.items() if len(sources) > 1
    }
    source_outcomes: dict[str, ProviderOutcome] = {}
    for source, source_page_list in source_pages.items():
        source_outcomes[source] = (outcomes or {}).get(source) or _aggregate_outcome(
            source, source_page_list
        )
    for source, outcome in (outcomes or {}).items():
        source_outcomes.setdefault(source, outcome)

    incomplete_sources = [
        source
        for source, outcome in source_outcomes.items()
        if outcome.complete is not True
        or outcome.status not in {ProviderOutcomeStatus.VALID, ProviderOutcomeStatus.EMPTY}
    ]
    complete = not truncated and not incomplete_sources and bool(source_outcomes)
    if truncated:
        reason = "max_results"
    elif incomplete_sources:
        reason = "source_incomplete:" + ",".join(sorted(incomplete_sources))
    elif not source_outcomes:
        reason = "no_sources"
    else:
        reason = None
    return FederatedSearchPage(
        results=selected,
        raw_result_count=len(rows),
        duplicate_count=duplicate_count,
        source_outcomes=source_outcomes,
        pages_fetched={source: len(items) for source, items in source_pages.items()},
        complete=complete,
        completeness_reason=reason,
        ordering=ordering,
        max_results=max_results,
        provider_plans=dict(plans or {}),
        duplicate_groups=duplicate_groups,
    )


def validate_federated_page(page: FederatedSearchPage) -> tuple[str, ...]:
    """Return deterministic quality issues for a merged federated page.

    The validator is deliberately non-mutating and conservative: it checks
    invariants that can be proven from the envelope (ordering, result caps,
    identity deduplication and completeness).  It does not turn an incomplete
    source into an error-free result and does not infer missing provider data.
    """

    issues: list[str] = []
    if page.raw_result_count < len(page.results):
        issues.append("raw_result_count_below_selected_results")
    if page.duplicate_count > page.raw_result_count:
        issues.append("duplicate_count_exceeds_raw_result_count")
    if len(page.results) > page.max_results:
        issues.append("result_cap_exceeded")

    identities = [_record_identity_key(result) for result in page.results]
    known = [identity for identity in identities if identity is not None]
    if len(known) != len(set(known)):
        issues.append("duplicate_identity_after_merge")

    rows = [("", 0, index, result, identities[index]) for index, result in enumerate(page.results)]
    keys = [_merge_sort_key(row, page.ordering) for row in rows]
    if keys != sorted(keys):
        issues.append("ordering_not_stable")

    if page.complete and page.completeness_reason is not None:
        issues.append("complete_page_has_completeness_reason")
    if not page.complete and page.completeness_reason is None:
        issues.append("incomplete_page_missing_completeness_reason")
    if set(page.pages_fetched) != set(page.source_outcomes):
        issues.append("source_outcome_page_partition_mismatch")
    return tuple(dict.fromkeys(issues))


def _aggregate_outcome(source: str, pages: tuple[SearchPage, ...]) -> ProviderOutcome:
    if not pages:
        return ProviderOutcome(
            provider=source,
            operation="search",
            status=ProviderOutcomeStatus.EMPTY_UNCONFIRMED,
            returned=0,
            complete=None,
        )
    returned = sum(len(page.results) for page in pages)
    has_incomplete = any(
        page.is_complete is False
        or page.access_status
        in {"access_control_required", "login_required", "secret_or_restricted"}
        or page.extraction_status in {"failed", "parser_contract_changed", "unsupported_format"}
        or _trace_retrieval_status(page) is not None
        for page in pages
    )
    all_complete = all(page.is_complete is True for page in pages)
    if any(
        page.access_status in {"access_control_required", "login_required", "secret_or_restricted"}
        for page in pages
    ):
        status = ProviderOutcomeStatus.BLOCKED
    elif any(
        page.extraction_status in {"failed", "parser_contract_changed", "unsupported_format"}
        for page in pages
    ):
        status = (
            ProviderOutcomeStatus.SCHEMA_INVALID
            if any(page.extraction_status == "parser_contract_changed" for page in pages)
            else ProviderOutcomeStatus.PARSER_CHANGED
        )
    elif any(_trace_retrieval_status(page) == "rate_limited" for page in pages):
        status = ProviderOutcomeStatus.RATE_LIMITED
    elif any(_trace_retrieval_status(page) == "timeout" for page in pages):
        status = ProviderOutcomeStatus.TIMEOUT
    elif any(_trace_retrieval_status(page) == "tls_error" for page in pages):
        status = ProviderOutcomeStatus.TLS_ERROR
    elif any(_trace_retrieval_status(page) == "source_unavailable" for page in pages):
        status = ProviderOutcomeStatus.UNAVAILABLE
    else:
        explicit_empty = all(page.is_explicit_empty for page in pages)
        if not returned and not explicit_empty:
            status = ProviderOutcomeStatus.EMPTY_UNCONFIRMED
        elif has_incomplete:
            status = ProviderOutcomeStatus.PARTIAL
        else:
            status = ProviderOutcomeStatus.VALID if returned else ProviderOutcomeStatus.EMPTY
    known_totals = [page.total for page in pages if page.total_known is True]
    return ProviderOutcome(
        provider=source,
        operation="search",
        status=status,
        retryable=status
        in {
            ProviderOutcomeStatus.RATE_LIMITED,
            ProviderOutcomeStatus.TIMEOUT,
            ProviderOutcomeStatus.UNAVAILABLE,
            ProviderOutcomeStatus.TLS_ERROR,
        },
        returned=returned,
        reported_total=max(known_totals, default=None),
        pagination_mode=pages[-1].pagination_mode,
        complete=False if has_incomplete else (True if all_complete else None),
        completeness_reason=pages[-1].completeness_reason,
        trace=pages[-1].source_trace,
    )


def _trace_retrieval_status(page: SearchPage) -> str | None:
    """Normalize transport status for aggregation without changing page data."""

    raw = page.source_trace.retrieval_status if page.source_trace is not None else None
    if raw in {"rate_limited", "http_429"}:
        return "rate_limited"
    if raw in {"timeout", "timed_out"}:
        return "timeout"
    if raw in {"tls_error", "ssl_error"}:
        return "tls_error"
    if raw in {"source_unavailable", "unavailable", "http_5xx"}:
        return "source_unavailable"
    return None


def _record_identity_key(record: Any) -> str | None:
    if isinstance(record, (CanonicalDecision, CanonicalDocument, CanonicalPrecedent)):
        identity = canonical_record_identity(record)
        cross_source = _cross_source_decision_key(record)
        return cross_source or _document_equivalence_key(record) or identity.key
    if isinstance(record, JurisprudenceResult):
        kind: Literal["decision", "precedent"] = (
            "precedent" if record.type.casefold() in {"precedent", "sumula", "tese"} else "decision"
        )
        identity = resolve_legal_identity(
            kind=kind,
            source=record.source,
            authority=record.court,
            native_id=record.id,
            case_number=record.number or "",
            record_type=record.type,
            event_date=record.judgment_date or record.publication_date or record.updated_at or "",
            text=record.full_text or record.summary or record.thesis or record.question or "",
        )
        return _cross_source_result_key(record) or _document_equivalence_key(record) or identity.key
    return None


def _document_equivalence_key(record: Any) -> str | None:
    """Return a conservative cross-source key for the same published text."""

    decision_type = str(
        getattr(record, "decision_type", None) or getattr(record, "type", None) or ""
    ).casefold()
    if re.search(r"republica|retifica|vers[aã]o", decision_type):
        return None
    authority = str(getattr(record, "court", "") or getattr(record, "authority", "") or "")
    event_date = str(
        getattr(record, "judgment_date", None)
        or getattr(record, "publication_date", None)
        or getattr(record, "updated_at", None)
        or ""
    )
    degree = str(getattr(record, "degree", None) or "")
    instance = str(getattr(record, "instance", None) or "")
    if not authority or not decision_type or not event_date:
        return None
    document_url = str(getattr(record, "document_url", None) or "").strip()
    if document_url:
        parsed = urlsplit(document_url)
        if parsed.scheme and parsed.netloc and parsed.path:
            location = f"{parsed.netloc.casefold()}{parsed.path}"
            return "equiv:document:" + _digest_equivalence(
                (authority, decision_type, event_date, degree, instance, location)
            )
    text = " ".join(
        str(getattr(record, field, None) or "")
        for field in ("full_text", "summary", "thesis", "question", "subject")
    )
    normalized = _normalize_equivalence_text(text)
    if len(normalized) < 120:
        return None
    return "equiv:text:" + _digest_equivalence(
        (authority, decision_type, event_date, degree, instance, normalized)
    )


def _normalize_equivalence_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", without_marks))


def _digest_equivalence(parts: tuple[str, ...]) -> str:
    payload = "|".join(_normalize_equivalence_text(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _cross_source_decision_key(
    record: CanonicalDecision | CanonicalDocument | CanonicalPrecedent,
) -> str | None:
    """Build a conservative cross-portal key when all legal dimensions exist."""

    if not isinstance(record, CanonicalDecision):
        return None
    number = str(record.case_number or "").strip()
    event_date = str(record.judgment_date or record.publication_date or "").strip()
    decision_type = str(record.decision_type or "").strip().casefold()
    court = str(record.court or "").strip().casefold()
    digits = re.sub(r"\D", "", number)
    if not court or not decision_type or not event_date or len(digits) != 20:
        return None
    return "cross:decision:" + "|".join((court, digits, decision_type, event_date))


def _cross_source_result_key(record: JurisprudenceResult) -> str | None:
    number = str(record.number or "").strip()
    event_date = str(record.judgment_date or record.publication_date or "").strip()
    record_type = str(record.type or "").strip().casefold()
    court = str(record.court or "").strip().casefold()
    digits = re.sub(r"\D", "", number)
    if not court or not record_type or not event_date or len(digits) != 20:
        return None
    return "cross:decision:" + "|".join((court, digits, record_type, event_date))


def _merge_sort_key(row: tuple[str, int, int, Any, str | None], ordering: str) -> tuple[Any, ...]:
    source, page_number, record_index, record, _identity_key = row
    record_id = str(getattr(record, "id", ""))
    if ordering == "source_id":
        return (source.casefold(), record_id, page_number, record_index)
    field_name = "publication_date" if ordering.startswith("published") else "updated_at"
    date_value = getattr(record, field_name, None) or ""
    normalized = normalize_date_value(date_value) if date_value else None
    ordinal = 0
    if normalized:
        try:
            from datetime import date

            ordinal = date.fromisoformat(normalized).toordinal()
        except ValueError:
            ordinal = 0
    descending = ordering.endswith("_desc")
    # Missing dates always sort after dated rows.  The remaining components are
    # ascending stable tie-breakers, independent of direction.
    return (
        0 if ordinal else 1,
        -ordinal if descending else ordinal,
        source.casefold(),
        record_id,
        page_number,
        record_index,
    )


def _filter_support(
    capability: ProviderCapabilities | None,
    name: str,
) -> FilterSupport:
    if capability is None:
        return FilterSupport.UNVERIFIED
    try:
        return FilterSupport(capability.filter_status(name))
    except ValueError:
        return FilterSupport.UNVERIFIED


__all__ = [
    "CURSOR_VERSION",
    "FederatedCursor",
    "FederatedSearchPage",
    "ProviderQueryPlan",
    "SearchIntent",
    "merge_federated_pages",
    "plan_federated_query",
    "validate_federated_page",
]
