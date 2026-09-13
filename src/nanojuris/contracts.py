"""Versioned, additive provider contract primitives.

The public provider classes predate a typed contract envelope.  This module
adds explicit semantics without changing their method signatures or turning an
unknown value into a negative assertion.  It is intentionally independent from
transport and parsers so adapters can adopt it one at a time.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from nanojuris.errors import safe_error_message
from nanojuris.models import SearchPage, SourceTrace


class FilterSupport(str, Enum):
    """Evidence level for one query filter."""

    NATIVE = "native"
    TRANSLATED = "translated"
    LOCAL_POSTFILTER = "local_postfilter"
    VALIDATED_SCOPE = "validated_scope"
    UNSUPPORTED = "unsupported"
    UNVERIFIED = "unverified"


class EvidenceKind(str, Enum):
    """Kinds of evidence used to establish a provider capability."""

    OFFICIAL_DOCUMENTATION = "official_documentation"
    NETWORK_CAPTURE = "network_capture"
    FIXTURE = "fixture"
    LIVE_CHECK = "live_check"
    TEST = "test"
    JUSCRAPER_REFERENCE = "juscraper_reference"


@dataclass(frozen=True, slots=True)
class CapabilityEvidence:
    """Redacted, addressable evidence for one contract assertion."""

    source: str
    kind: EvidenceKind
    reference: str
    captured_at: str
    fingerprint: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.reference.strip():
            raise ValueError("source and reference must not be empty")
        if not self.captured_at.strip():
            raise ValueError("captured_at must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "kind": self.kind.value,
            "reference": self.reference,
            "captured_at": self.captured_at,
            "fingerprint": self.fingerprint,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class FieldContract:
    """Canonical field declaration with explicit normalization semantics."""

    name: str
    value_type: str = "string"
    required: bool = False
    normalized: bool = True
    provenance: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.value_type.strip():
            raise ValueError("field name and value_type must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DocumentContract:
    """Document capability without implying that a source publishes text."""

    document_type: str
    access: str = "unknown"
    content_types: tuple[str, ...] = ()
    endpoint: str | None = None
    requires_fetch: bool = False
    ocr_allowed: bool = False

    def __post_init__(self) -> None:
        if not self.document_type.strip() or not self.access.strip():
            raise ValueError("document_type and access must not be empty")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["content_types"] = list(self.content_types)
        return payload


CANONICAL_FILTERS: tuple[str, ...] = (
    "text",
    "courts",
    "types",
    "all_words",
    "any_words",
    "without_words",
    "exact_phrase",
    "rapporteur",
    "updated_from",
    "updated_to",
    "published_from",
    "published_to",
    "number",
    "party_name",
    "party_document",
    "lawyer_name",
    "oab",
    "precatory_number",
    "police_document",
    "cda",
    "source_origin",
    "source_origins",
    "fetch_details",
    "case_class",
    "judging_body",
    "degree",
    "instance",
    "branch",
    "legal_area",
    "authority",
    "collection",
    "document_type",
    "decision_type",
    "judgment_date_from",
    "judgment_date_to",
    "election_year",
    "observations",
    "tags",
    "municipality",
    "publication_source",
    "publication_number",
    "publication_volume",
    "uf",
)


@dataclass(frozen=True, slots=True)
class CanonicalFilterRegistry:
    """Canonical names and provider aliases used by contract translation."""

    aliases: Mapping[str, str]

    @classmethod
    def default(cls) -> CanonicalFilterRegistry:
        aliases = {name: name for name in CANONICAL_FILTERS}
        aliases.update(
            {
                "court": "courts",
                "court_code": "courts",
                "from_date": "published_from",
                "to_date": "published_to",
                "class": "case_class",
                "organ": "judging_body",
                "tribunal": "authority",
                "ano_eleicao": "election_year",
                "observacoes": "observations",
                "etiquetas": "tags",
                "municipio": "municipality",
                "fonte_publicacao": "publication_source",
                "numero_publicacao": "publication_number",
                "volume_publicacao": "publication_volume",
            }
        )
        return cls(aliases=aliases)

    def canonicalize(self, name: str) -> str | None:
        """Return canonical name, or ``None`` for an unknown alias."""

        return self.aliases.get(name.strip().lower())

    def to_dict(self) -> dict[str, str]:
        return dict(self.aliases)


class ProviderOutcomeStatus(str, Enum):
    """Mutually exclusive outcome states for one provider operation."""

    VALID = "valid"
    EMPTY = "empty"
    EMPTY_UNCONFIRMED = "empty_unconfirmed"
    PARTIAL = "partial"
    INVALID_QUERY = "invalid_query"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    TLS_ERROR = "tls_error"
    PARSER_CHANGED = "parser_changed"
    SCHEMA_INVALID = "schema_invalid"


class SearchOutcomeStatus(str, Enum):
    """Mutually exclusive outcomes exposed by the intelligent live search."""

    SUCCESS_WITH_RESULTS = "success_with_results"
    AUTHORITATIVE_EMPTY = "authoritative_empty"
    UNCONFIRMED_EMPTY = "unconfirmed_empty"
    TIMEOUT = "timeout"
    ACCESS_BLOCKED = "access_blocked"
    RATE_LIMITED = "rate_limited"
    TRANSPORT_ERROR = "transport_error"
    SCHEMA_INVALID = "schema_invalid"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class FilterContract:
    """Contract evidence for a single filter exposed by a provider."""

    name: str
    support: FilterSupport = FilterSupport.UNVERIFIED
    native_name: str | None = None
    evidence: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("filter name must not be empty")
        if self.native_name is not None and not self.native_name.strip():
            raise ValueError("native_name must not be blank when provided")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["support"] = self.support.value
        return payload


@dataclass(frozen=True, slots=True)
class ProviderOutcome:
    """Safe, serializable result envelope for one provider operation."""

    provider: str
    operation: str
    status: ProviderOutcomeStatus
    retryable: bool = False
    returned: int = 0
    reported_total: int | None = None
    pagination_mode: str | None = None
    complete: bool | None = None
    completeness_reason: str | None = None
    error_type: str | None = None
    message: str | None = None
    trace: SourceTrace | None = None

    def __post_init__(self) -> None:
        if not self.provider.strip() or not self.operation.strip():
            raise ValueError("provider and operation must not be empty")
        if self.returned < 0:
            raise ValueError("returned must be non-negative")
        if self.reported_total is not None and self.reported_total < 0:
            raise ValueError("reported_total must be non-negative")
        if self.message:
            object.__setattr__(self, "message", safe_error_message(self.message))

    @classmethod
    def from_page(cls, page: SearchPage, *, operation: str = "search") -> ProviderOutcome:
        """Create an outcome while preserving the page's completeness state."""

        status = ProviderOutcomeStatus.VALID if page.results else ProviderOutcomeStatus.EMPTY
        retrieval_status = (
            page.source_trace.retrieval_status if page.source_trace is not None else None
        )
        if page.access_status in {
            "access_control_required",
            "login_required",
            "secret_or_restricted",
        }:
            status = ProviderOutcomeStatus.BLOCKED
        elif retrieval_status in {"timeout", "timed_out"}:
            status = ProviderOutcomeStatus.TIMEOUT
        elif retrieval_status in {"tls_error", "ssl_error"}:
            status = ProviderOutcomeStatus.TLS_ERROR
        elif retrieval_status in {"rate_limited", "http_429"}:
            status = ProviderOutcomeStatus.RATE_LIMITED
        elif retrieval_status in {"source_unavailable", "unavailable", "http_5xx"}:
            status = ProviderOutcomeStatus.UNAVAILABLE
        elif page.extraction_status in {"failed", "unsupported_format"}:
            status = ProviderOutcomeStatus.PARSER_CHANGED
        elif page.extraction_status == "parser_contract_changed":
            status = ProviderOutcomeStatus.SCHEMA_INVALID
        elif not page.results and not page.is_explicit_empty:
            # ``total=0`` is a legacy sentinel for several providers.  Keep an
            # unproven empty page distinct from an explicitly complete empty
            # result so federation and validation cannot claim a false zero.
            status = ProviderOutcomeStatus.EMPTY_UNCONFIRMED
        elif page.is_complete is False:
            status = ProviderOutcomeStatus.PARTIAL
        return cls(
            provider=page.source,
            operation=operation,
            status=status,
            retryable=status
            in {
                ProviderOutcomeStatus.RATE_LIMITED,
                ProviderOutcomeStatus.TIMEOUT,
                ProviderOutcomeStatus.UNAVAILABLE,
                ProviderOutcomeStatus.TLS_ERROR,
            },
            returned=len(page.results),
            # ``None`` is the v2 representation for a provider that has not
            # proved its remote count.  Keep legacy totals only when explicit.
            reported_total=page.total if page.total_known is True else None,
            pagination_mode=page.pagination_mode,
            complete=page.is_complete,
            completeness_reason=page.completeness_reason,
            trace=page.source_trace,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        if self.trace is not None:
            payload["trace"] = self.trace.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class SearchSourceOutcome:
    """Bounded source telemetry without provider payload or credentials."""

    provider: str
    status: SearchOutcomeStatus
    latency_ms: float | None = None
    pages: int = 0
    candidate_count: int = 0
    total_state: str = "unknown"
    filters_applied: dict[str, str] = field(default_factory=dict)
    message: str | None = None
    trace: SourceTrace | None = None

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        if self.pages < 0 or self.candidate_count < 0:
            raise ValueError("pages and candidate_count must be non-negative")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
        if self.total_state not in {"zero", "known", "unknown"}:
            raise ValueError("total_state must be zero, known or unknown")
        if self.message:
            object.__setattr__(self, "message", safe_error_message(self.message))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        if self.trace is not None:
            payload["trace"] = self.trace.to_dict()
        return payload


def search_outcome_from_page(
    page: SearchPage,
    *,
    latency_ms: float | None = None,
    pages: int = 1,
) -> SearchSourceOutcome:
    """Classify a page without conflating external failure and empty search."""

    access = _enum_value(page.access_status)
    extraction = _enum_value(page.extraction_status)
    retrieval = page.source_trace.retrieval_status if page.source_trace else None
    if access in {"access_control_required", "login_required", "secret_or_restricted"}:
        status = SearchOutcomeStatus.ACCESS_BLOCKED
    elif retrieval in {"timeout", "timed_out"}:
        status = SearchOutcomeStatus.TIMEOUT
    elif retrieval in {"rate_limited", "http_429"}:
        status = SearchOutcomeStatus.RATE_LIMITED
    elif retrieval in {"tls_error", "ssl_error", "source_unavailable", "unavailable"}:
        status = SearchOutcomeStatus.TRANSPORT_ERROR
    elif extraction in {"failed", "parser_contract_changed", "unsupported_format"}:
        status = SearchOutcomeStatus.SCHEMA_INVALID
    elif page.results and page.is_complete is False:
        status = SearchOutcomeStatus.PARTIAL
    elif page.results:
        status = SearchOutcomeStatus.SUCCESS_WITH_RESULTS
    elif page.is_explicit_empty:
        status = SearchOutcomeStatus.AUTHORITATIVE_EMPTY
    else:
        status = SearchOutcomeStatus.UNCONFIRMED_EMPTY
    if page.total_known is True and page.total == 0:
        total_state = "zero"
    elif page.total_known is True:
        total_state = "known"
    else:
        total_state = "unknown"
    return SearchSourceOutcome(
        provider=page.source,
        status=status,
        latency_ms=latency_ms,
        pages=pages,
        candidate_count=len(page.results),
        total_state=total_state,
        filters_applied=dict(page.filters_applied),
        # Access diagnostics take precedence over a generic completeness
        # explanation.  This preserves per-source failure context (for
        # example an explicit TRE authority batch with one blocked UF) in the
        # federated envelope instead of presenting it as an unexplained
        # partial result.
        message=page.access_reason or page.completeness_reason,
        trace=page.source_trace,
    )


def search_outcome_from_error(
    provider: str,
    error_type: str,
    *,
    message: str | None = None,
) -> SearchSourceOutcome:
    """Map a sanitized execution error to one explicit source outcome."""

    normalized = error_type.casefold()
    if "timeout" in normalized:
        status = SearchOutcomeStatus.TIMEOUT
    elif "access" in normalized or "captcha" in normalized or "login" in normalized:
        status = SearchOutcomeStatus.ACCESS_BLOCKED
    elif "rate" in normalized or "429" in normalized:
        status = SearchOutcomeStatus.RATE_LIMITED
    elif "parser" in normalized or "schema" in normalized:
        status = SearchOutcomeStatus.SCHEMA_INVALID
    else:
        status = SearchOutcomeStatus.TRANSPORT_ERROR
    return SearchSourceOutcome(provider=provider, status=status, message=message)


def _enum_value(value: object) -> str | None:
    if value is None:
        return None
    raw = getattr(value, "value", value)
    return str(raw)


def filter_contracts_for(
    *,
    supported: list[str] | tuple[str, ...] = (),
    unsupported: list[str] | tuple[str, ...] = (),
    explicit: dict[str, FilterContract | FilterSupport | str] | None = None,
) -> dict[str, FilterContract]:
    """Build a deterministic v2 map from legacy lists plus explicit evidence.

    Explicit entries win over legacy lists.  Legacy ``supported_filters`` are
    represented as native and legacy ``unsupported_filters`` as unsupported;
    every other name remains absent and therefore unverified.
    """

    result: dict[str, FilterContract] = {}
    for name in sorted(set(supported)):
        result[name] = FilterContract(name=name, support=FilterSupport.NATIVE)
    for name in sorted(set(unsupported)):
        result.setdefault(name, FilterContract(name=name, support=FilterSupport.UNSUPPORTED))
    for name, value in sorted((explicit or {}).items()):
        if isinstance(value, FilterContract):
            if value.name != name:
                raise ValueError("explicit filter key and contract name differ")
            result[name] = value
        else:
            result[name] = FilterContract(name=name, support=FilterSupport(value))
    return result


__all__ = [
    "CANONICAL_FILTERS",
    "CapabilityEvidence",
    "CanonicalFilterRegistry",
    "DocumentContract",
    "EvidenceKind",
    "FieldContract",
    "FilterContract",
    "FilterSupport",
    "ProviderOutcome",
    "ProviderOutcomeStatus",
    "SearchOutcomeStatus",
    "SearchSourceOutcome",
    "filter_contracts_for",
    "search_outcome_from_error",
    "search_outcome_from_page",
]
