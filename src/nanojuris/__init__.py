"""NanoJuris public API."""

from __future__ import annotations

from nanojuris.brazil import (
    COURTS,
    CourtBranch,
    CourtInfo,
    ImplementationStatus,
    SourceSystem,
    get_court,
    list_courts,
    normalize_court_code,
)
from nanojuris.canonical import (
    result_to_canonical_decision,
    result_to_canonical_precedent,
    search_page_to_canonical,
)
from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import NetworkConfigurationError, QueryRejectedError, UnsupportedQueryError
from nanojuris.extraction import FetchedContent, FetchRequest, HttpFetcher, ParsedContent
from nanojuris.health import (
    ProviderHealthReport,
    ProviderHealthStatus,
    check_provider,
    check_sources,
)
from nanojuris.models import (
    AccessStatus,
    CanonicalDecision,
    CanonicalDocument,
    CanonicalPrecedent,
    DecisionBundle,
    ExtractionStatus,
    ExtractionTrace,
    JurisprudenceQuery,
    JurisprudenceResult,
    ParadigmCase,
    ProviderCapabilities,
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.source_contracts import (
    SourceContractAssessment,
    assess_source_contract,
    assess_source_contracts,
    contracts_payload,
    summarize_contracts,
)
from nanojuris.store import CanonicalStore, ResearchRun, SQLiteStore, StoreStats

__all__ = [
    "AccessStatus",
    "assess_source_contract",
    "assess_source_contracts",
    "CanonicalDecision",
    "CanonicalDocument",
    "CanonicalPrecedent",
    "CanonicalStore",
    "contracts_payload",
    "COURTS",
    "CourtBranch",
    "CourtInfo",
    "DecisionBundle",
    "ExtractionStatus",
    "ExtractionTrace",
    "FetchedContent",
    "FetchRequest",
    "HttpFetcher",
    "ImplementationStatus",
    "get_court",
    "JurisprudenceQuery",
    "JurisprudenceResult",
    "list_courts",
    "NanoJurisClient",
    "NanoJurisConfig",
    "NetworkConfigurationError",
    "normalize_court_code",
    "ParadigmCase",
    "ParsedContent",
    "ProviderHealthReport",
    "ProviderHealthStatus",
    "ProviderCapabilities",
    "ProviderCatalog",
    "ProviderOption",
    "QueryRejectedError",
    "ResearchRun",
    "result_to_canonical_decision",
    "result_to_canonical_precedent",
    "SearchPage",
    "search_page_to_canonical",
    "check_provider",
    "check_sources",
    "SourceTrace",
    "SourceSystem",
    "SourceContractAssessment",
    "SQLiteStore",
    "StoreStats",
    "UnsupportedQueryError",
    "summarize_contracts",
]

__version__ = "0.3.0"
