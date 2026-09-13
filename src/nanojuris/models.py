"""Typed data contracts for jurisprudence and precedent sources."""

from __future__ import annotations

import base64
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

_FILTER_SUPPORT_VALUES = {
    "native",
    "translated",
    "local_postfilter",
    "validated_scope",
    "unsupported",
    "unverified",
}


def utc_now_iso() -> str:
    """Return a stable UTC timestamp for source traces."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class AccessStatus(str, Enum):
    """Normalized public-source access status."""

    PUBLIC = "public"
    PARTIAL = "partial"
    ACCESS_CONTROL_REQUIRED = "access_control_required"
    LOGIN_REQUIRED = "login_required"
    SECRET_OR_RESTRICTED = "secret_or_restricted"
    NOT_FOUND = "not_found"
    SOURCE_UNAVAILABLE = "source_unavailable"


class ExtractionStatus(str, Enum):
    """Normalized extraction outcome status."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    EMPTY = "empty"
    PARSER_CONTRACT_CHANGED = "parser_contract_changed"
    UNSUPPORTED_FORMAT = "unsupported_format"
    FAILED = "failed"


@dataclass(slots=True)
class ProviderCapabilities:
    """Declared extraction capabilities and limits for a public source."""

    source: str
    display_name: str
    source_url: str
    category: str
    search_modes: list[str] = field(default_factory=list)
    document_types: list[str] = field(default_factory=list)
    content_formats: list[str] = field(default_factory=list)
    canonical_records: list[str] = field(default_factory=list)
    semantic_discriminator: str | None = None
    extracted_fields: list[str] = field(default_factory=list)
    access_statuses: list[AccessStatus] = field(default_factory=list)
    endpoints: list[str] = field(default_factory=list)
    supports_full_text: bool = False
    supports_catalog: bool = False
    supports_suggestions: bool = False
    supports_live_tests: bool = False
    supports_cli: bool = False
    supports_unified_search: bool = False
    # A provider may be technically ready but intentionally withheld from the
    # default federation until an explicit rollout/legal decision is supplied
    # in ``NanoJurisConfig.unified_opt_in_sources``.
    opt_in_unified_search: bool = False
    supports_mcp: bool = False
    supports_studio: bool = False
    pagination_mode: str = "unknown"
    max_remote_page: int | None = None
    max_remote_page_size: int | None = None
    completeness_contract: str = "unknown"
    full_text_access: str = "unknown"
    supported_filters: list[str] = field(default_factory=list)
    unsupported_filters: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    responsible_use: list[str] = field(default_factory=list)
    # Explicit v2 semantics for filters.  The legacy lists above remain the
    # source-compatible surface; this map is additive and accepts the values
    # native, translated, local_postfilter, unsupported and unverified.
    filter_semantics: dict[str, str] = field(default_factory=dict)
    ordering_modes: list[str] = field(default_factory=list)
    detail_modes: list[str] = field(default_factory=list)

    def filter_status(self, name: str) -> str:
        """Return the v2 support status for a filter without false certainty."""

        explicit = self.filter_semantics.get(name)
        if explicit in _FILTER_SUPPORT_VALUES:
            return explicit
        if name in self.supported_filters:
            return "native"
        if name in self.unsupported_filters:
            return "unsupported"
        return "unverified"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SourceTrace:
    """Technical trace of a public source request."""

    provider: str
    endpoint: str
    retrieved_at: str = field(default_factory=utc_now_iso)
    query: dict[str, Any] = field(default_factory=dict)
    source_url: str | None = None
    limitations: list[str] = field(default_factory=list)
    http_status: int | None = None
    final_url: str | None = None
    content_type: str | None = None
    content_sha256: str | None = None
    response_bytes: int | None = None
    elapsed_ms: float | None = None
    retrieval_status: str | None = None
    transformations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExtractionTrace:
    """Technical trace of a parser/extractor run."""

    parser: str
    parser_version: str
    status: ExtractionStatus = ExtractionStatus.COMPLETE
    access_status: AccessStatus = AccessStatus.PARTIAL
    extracted_at: str = field(default_factory=utc_now_iso)
    content_sha256: str | None = None
    content_bytes: int | None = None
    warnings: list[str] = field(default_factory=list)
    transformations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CanonicalDocument:
    """A public document extracted from a jurisprudence source."""

    id: str
    source: str
    document_type: str
    content_type: str | None = None
    title: str | None = None
    text: str | None = None
    raw_bytes: bytes | None = field(default=None, repr=False, compare=False)
    url: str | None = None
    sha256: str | None = None
    byte_size: int | None = None
    retrieved_at: str | None = None
    access_status: AccessStatus = AccessStatus.PARTIAL
    extraction_status: ExtractionStatus = ExtractionStatus.PARTIAL
    source_trace: SourceTrace | None = None
    extraction_trace: ExtractionTrace | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    # Structural/document quality facts are additive and remain optional for
    # HTML and text responses. OCR confidence is populated only by an
    # explicitly configured OCR adapter with a measured value.
    page_count: int | None = None
    ocr_confidence: float | None = None

    def to_dict(self, *, include_raw_bytes: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        raw_bytes = payload.pop("raw_bytes", None)
        payload["raw_bytes_preserved"] = raw_bytes is not None
        if include_raw_bytes and raw_bytes is not None:
            payload["raw_bytes_base64"] = base64.b64encode(raw_bytes).decode("ascii")
        return payload


@dataclass(slots=True)
class CanonicalDecision:
    """A normalized decision extracted from a jurisprudence source."""

    id: str
    source: str
    court: str
    case_number: str | None = None
    registry_number: str | None = None
    decision_type: str | None = None
    case_class: str | None = None
    subject: str | None = None
    rapporteur: str | None = None
    judging_body: str | None = None
    origin_county: str | None = None
    judgment_date: str | None = None
    publication_date: str | None = None
    judgment_date_raw: str | None = None
    publication_date_raw: str | None = None
    source_updated_at: str | None = None
    source_updated_at_raw: str | None = None
    retrieved_at: str | None = None
    access_status: AccessStatus = AccessStatus.PARTIAL
    extraction_status: ExtractionStatus = ExtractionStatus.PARTIAL
    summary: str | None = None
    full_text: str | None = None
    document_url: str | None = None
    source_trace: SourceTrace | None = None
    extraction_trace: ExtractionTrace | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    # Semantic dimensions are optional and additive. Providers must only
    # populate them when the source exposes an auditable value; otherwise the
    # original value remains in ``raw`` and the field stays ``None``. Appending
    # these fields preserves historical positional construction.
    degree: str | None = None
    instance: str | None = None
    branch: str | None = None
    legal_area: str | None = None
    authority: str | None = None
    collection: str | None = None
    document_type: str | None = None
    source_origin: str | None = None
    field_provenance: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CanonicalPrecedent:
    """A normalized qualified precedent extracted from a public source."""

    id: str
    source: str
    court: str
    precedent_type: str
    number: str | int | None = None
    status: str | None = None
    question: str | None = None
    thesis: str | None = None
    affected_cases: list[ParadigmCase] = field(default_factory=list)
    paradigm_cases: list[ParadigmCase] = field(default_factory=list)
    updated_at: str | None = None
    updated_at_raw: str | None = None
    source_updated_at: str | None = None
    source_updated_at_raw: str | None = None
    retrieved_at: str | None = None
    access_status: AccessStatus = AccessStatus.PARTIAL
    extraction_status: ExtractionStatus = ExtractionStatus.PARTIAL
    source_trace: SourceTrace | None = None
    extraction_trace: ExtractionTrace | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    degree: str | None = None
    instance: str | None = None
    branch: str | None = None
    legal_area: str | None = None
    authority: str | None = None
    collection: str | None = None
    document_type: str | None = None
    source_origin: str | None = None
    field_provenance: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ParadigmCase:
    """A process linked to a precedent."""

    number: str
    case_class: str | int | None = None
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class JurisprudenceQuery:
    """Unified query object for jurisprudence providers."""

    text: str = ""
    all_words: str = ""
    any_words: str = ""
    without_words: str = ""
    exact_phrase: str = ""
    updated_from: str = ""
    updated_to: str = ""
    published_from: str = ""
    published_to: str = ""
    include_cancelled: bool = False
    order_by: str = "Text"
    number: str = ""
    rapporteur: str = ""
    party_name: str = ""
    party_document: str = ""
    lawyer_name: str = ""
    oab: str = ""
    precatory_number: str = ""
    police_document: str = ""
    cda: str = ""
    source_origin: str = ""
    source_origins: list[str] = field(default_factory=list)
    fetch_details: bool = False
    courts: list[str] = field(default_factory=list)
    types: list[str] = field(default_factory=list)
    page: int = 1
    page_size: int = 10
    # Canonical refinement filters. They are optional to preserve the v1
    # constructor and are translated only when a provider declares support.
    case_class: str = ""
    judging_body: str = ""
    degree: str = ""
    instance: str = ""
    branch: str = ""
    legal_area: str = ""
    authority: str = ""
    collection: str = ""
    document_type: str = ""
    decision_type: str = ""
    judgment_date_from: str = ""
    judgment_date_to: str = ""
    # Official SJUR/TRE refinements.  They remain optional so providers that
    # do not advertise the corresponding contract reject them explicitly
    # instead of silently dropping a federated filter.
    election_year: str = ""
    observations: str = ""
    tags: str = ""
    municipality: str = ""
    publication_source: str = ""
    publication_number: str = ""
    publication_volume: str = ""
    uf: str = ""

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page deve ser maior ou igual a 1")
        if self.page_size < 1 or self.page_size > 100:
            raise ValueError("page_size deve estar entre 1 e 100")
        for field_name in (
            "updated_from",
            "updated_to",
            "published_from",
            "published_to",
            "judgment_date_from",
            "judgment_date_to",
        ):
            value = getattr(self, field_name)
            if value and not _is_supported_query_date(value):
                raise ValueError(f"{field_name} deve usar YYYY-MM-DD ou DD/MM/YYYY")
        _validate_date_range(self.updated_from, self.updated_to, "updated")
        _validate_date_range(self.published_from, self.published_to, "published")
        _validate_date_range(self.judgment_date_from, self.judgment_date_to, "judgment_date")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_supported_query_date(value: str) -> bool:
    """Validate the date formats accepted by provider query contracts."""

    return _parse_supported_query_date(value) is not None


def _parse_supported_query_date(value: str) -> datetime | None:
    """Parse a supported query date without changing its public representation."""

    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    return None


def _validate_date_range(start: str, end: str, field_prefix: str) -> None:
    """Reject an inverted date range before it reaches a provider."""

    if not start or not end:
        return
    parsed_start = _parse_supported_query_date(start)
    parsed_end = _parse_supported_query_date(end)
    if parsed_start is not None and parsed_end is not None and parsed_start > parsed_end:
        raise ValueError(f"{field_prefix}_from nao pode ser posterior a {field_prefix}_to")


@dataclass(slots=True)
class JurisprudenceResult:
    """A normalized result from a jurisprudence or precedent source."""

    id: str
    source: str
    court: str
    type: str
    number: str | int | None = None
    question: str | None = None
    thesis: str | None = None
    summary: str | None = None
    full_text: str | None = None
    status: str | None = None
    rapporteur: str | None = None
    updated_at: str | None = None
    judgment_date: str | None = None
    publication_date: str | None = None
    source_updated_at: str | None = None
    retrieved_at: str | None = None
    access_status: AccessStatus | None = None
    extraction_status: ExtractionStatus = ExtractionStatus.COMPLETE
    paradigm_cases: list[ParadigmCase] = field(default_factory=list)
    highlights: dict[str, str] = field(default_factory=dict)
    source_trace: SourceTrace | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    # Appended fields preserve positional construction of the v1 result.
    case_class: str | None = None
    judging_body: str | None = None
    degree: str | None = None
    instance: str | None = None
    branch: str | None = None
    legal_area: str | None = None
    authority: str | None = None
    collection: str | None = None
    document_type: str | None = None
    source_origin: str | None = None
    document_url: str | None = None
    field_provenance: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SearchPage:
    """A page of normalized results."""

    source: str
    total: int
    start: int
    end: int
    page: int
    page_size: int
    results: list[JurisprudenceResult]
    aggregations: dict[str, Any] = field(default_factory=dict)
    source_trace: SourceTrace | None = None
    pagination_mode: str = "unknown"
    is_complete: bool | None = None
    completeness_reason: str | None = None
    # Optional v2 metadata.  Appended fields keep historical positional
    # constructors valid while allowing cursor-based sources to be explicit.
    cursor: str | None = None
    ordering: str | None = None
    filters_applied: dict[str, str] = field(default_factory=dict)
    # ``None`` means the provider did not prove whether the remote total is
    # authoritative. This prevents legacy ``0`` from being treated as an
    # explicit empty result by federation.
    total_known: bool | None = None
    access_status: AccessStatus | None = None
    extraction_status: ExtractionStatus | None = None
    access_reason: str | None = None

    @property
    def effective_total(self) -> int | None:
        """Return the remote count only when the provider marked it known."""

        return self.total if self.total_known is True else None

    @property
    def is_explicit_empty(self) -> bool:
        """Whether this page is proven to be an empty result, not a failure."""

        return not self.results and (
            self.is_complete is True or (self.total_known is True and self.total == 0)
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DecisionBundle:
    """Decision texts linked to a precedent."""

    precedent_id: str
    source: str
    rapporteur: str | None = None
    procedural_follow_url: str | None = None
    texts: list[dict[str, Any]] = field(default_factory=list)
    source_trace: SourceTrace | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    raw_bytes: bytes | None = field(default=None, repr=False, compare=False)

    def to_dict(self, *, include_raw_bytes: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        raw_bytes = payload.pop("raw_bytes", None)
        payload["raw_bytes_preserved"] = raw_bytes is not None
        if include_raw_bytes and raw_bytes is not None:
            payload["raw_bytes_base64"] = base64.b64encode(raw_bytes).decode("ascii")
        return payload


@dataclass(slots=True)
class ProviderOption:
    """Normalized option exposed by a public provider catalog."""

    code: str
    description: str
    alias: str | None = None
    disabled: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProviderCatalog:
    """Normalized catalog of courts, precedent species and provider metadata."""

    source: str
    courts: list[ProviderOption] = field(default_factory=list)
    species: list[ProviderOption] = field(default_factory=list)
    species_groups: list[dict[str, Any]] = field(default_factory=list)
    source_trace: SourceTrace | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
