"""Source routing helpers for unified jurisprudence searches."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from nanojuris.models import ProviderCapabilities

CNJ_NUMBER_RE = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")

JURISPRUDENCE_CATEGORIES = {
    "administrative_jurisprudence",
    "court_jurisprudence",
    "court_precedents",
    "electoral_jurisprudence",
    "jurisprudence",
    "qualified_precedents",
}

IDENTIFIER_FILTERS = {
    "number",
    "party_name",
    "party_document",
    "lawyer_name",
    "oab",
    "precatory_number",
    "police_document",
    "cda",
}


@dataclass(frozen=True, slots=True)
class SourceSkip:
    """A source that should not be called for the current unified query."""

    source: str
    category: str
    reason: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "category": self.category,
            "reason": self.reason,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class RoutedSources:
    """Selected sources split into callable and intentionally skipped groups."""

    searched: list[str]
    skipped: list[SourceSkip]


@dataclass(frozen=True, slots=True)
class RoutingSummaryItem:
    """Human-readable routing explanation for agents and CLI users."""

    source: str
    action: str
    reason: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "action": self.action,
            "reason": self.reason,
            "message": self.message,
        }


def route_unified_sources(
    *,
    selected_sources: list[str],
    capabilities: dict[str, ProviderCapabilities],
    text: str,
    filters: dict[str, Any],
) -> RoutedSources:
    """Return sources that fit a unified jurisprudence query.

    The router is intentionally conservative: it avoids calls that are known to
    be semantically invalid, but it does not hide source failures for providers
    that are valid candidates for the user's question.
    """

    identifier_filters = _identifier_filters(text=text, filters=filters)
    has_identifier = bool(identifier_filters)
    searched: list[str] = []
    skipped: list[SourceSkip] = []

    for source in selected_sources:
        capability = capabilities.get(source)
        if capability is None:
            searched.append(source)
            continue

        skip = _skip_reason(
            capability,
            has_identifier=has_identifier,
            identifier_filters=identifier_filters,
        )
        if skip is None:
            searched.append(source)
        else:
            skipped.append(skip)

    return RoutedSources(searched=searched, skipped=skipped)


def build_routing_summary(
    *,
    routed: RoutedSources,
    capabilities: dict[str, ProviderCapabilities],
    errors: list[dict[str, str]],
) -> list[RoutingSummaryItem]:
    """Build a concise explanation of routing decisions."""

    summary: list[RoutingSummaryItem] = []
    failed_sources = {error["source"] for error in errors}
    for source in routed.searched:
        capability = capabilities.get(source)
        if source in failed_sources:
            continue
        summary.append(
            RoutingSummaryItem(
                source=source,
                action="searched",
                reason="source_applicable",
                message=_searched_message(capability),
            )
        )
    for skip in routed.skipped:
        summary.append(
            RoutingSummaryItem(
                source=skip.source,
                action="skipped",
                reason=skip.reason,
                message=skip.message,
            )
        )
    for error in errors:
        summary.append(
            RoutingSummaryItem(
                source=error["source"],
                action="failed",
                reason=error["error_type"],
                message=error["message"],
            )
        )
    return summary


def _skip_reason(
    capability: ProviderCapabilities,
    *,
    has_identifier: bool,
    identifier_filters: set[str],
) -> SourceSkip | None:
    if not capability.supports_unified_search:
        return SourceSkip(
            source=capability.source,
            category=capability.category,
            reason="unified_search_not_supported",
            message="A fonte nao declara suporte explicito a busca unificada.",
        )

    if capability.category == "case_lookup" and not has_identifier:
        return SourceSkip(
            source=capability.source,
            category=capability.category,
            reason="case_lookup_requires_identifier",
            message=(
                "Consulta processual exige numero CNJ, parte, documento, OAB "
                "ou outro identificador; nao e uma busca textual de jurisprudencia."
            ),
        )
    if capability.category == "case_lookup":
        return None

    unsupported_identifiers = (
        identifier_filters.difference(capability.supported_filters)
        if capability.supported_filters
        else set()
    )
    if unsupported_identifiers:
        labels = ", ".join(sorted(unsupported_identifiers))
        return SourceSkip(
            source=capability.source,
            category=capability.category,
            reason="identifier_filter_not_supported",
            message=(
                f"A fonte nao declara suporte ao filtro identificador: {labels}. "
                "Ela foi pulada para evitar resultados textuais sem correspondencia exata."
            ),
        )

    if capability.category == "judicial_communications":
        return SourceSkip(
            source=capability.source,
            category=capability.category,
            reason="not_jurisprudence_source",
            message=(
                "A fonte retorna comunicacoes/intimacoes judiciais, nao julgados "
                "de jurisprudencia para estudo jurimetrico."
            ),
        )

    if capability.category not in JURISPRUDENCE_CATEGORIES:
        return SourceSkip(
            source=capability.source,
            category=capability.category,
            reason="category_not_applicable",
            message="A categoria declarada da fonte nao pertence ao escopo de jurisprudencia.",
        )

    return None


def _identifier_filters(*, text: str, filters: dict[str, Any]) -> set[str]:
    """Return identifier filters that must be honored by a source."""

    requested = {name for name in IDENTIFIER_FILTERS if _has_value(filters.get(name))}
    if CNJ_NUMBER_RE.search(text):
        requested.add("number")
    return requested


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list | tuple | set):
        return bool(value)
    return bool(value)


def _searched_message(capability: ProviderCapabilities | None) -> str:
    if capability is None:
        return "A fonte foi consultada porque foi solicitada explicitamente."
    if capability.category == "case_lookup":
        return "A fonte foi consultada porque havia identificador processual suficiente."
    if capability.category == "qualified_precedents":
        return "A fonte foi consultada por cobrir precedentes qualificados."
    if capability.category == "court_precedents":
        return "A fonte foi consultada por cobrir precedentes do tribunal."
    if capability.category == "administrative_jurisprudence":
        return "A fonte foi consultada por cobrir jurisprudencia administrativa publica."
    if capability.category == "electoral_jurisprudence":
        return "A fonte foi consultada por cobrir jurisprudencia eleitoral publica."
    return "A fonte foi consultada por cobrir jurisprudencia textual publica."
