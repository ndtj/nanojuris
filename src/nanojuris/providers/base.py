"""Provider contract for jurisprudence sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from nanojuris.models import (
    AccessStatus,
    CanonicalDocument,
    DecisionBundle,
    JurisprudenceQuery,
    ProviderCapabilities,
    ProviderCatalog,
    SearchPage,
)


class JurisprudenceProvider(ABC):
    """Base class for public jurisprudence providers."""

    name: str

    @abstractmethod
    def search(self, query: JurisprudenceQuery) -> SearchPage:
        """Search the provider and return a normalized page."""

    @abstractmethod
    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        """Return decision texts or metadata linked to a precedent."""

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Return one public document when the provider supports full text."""

        raise NotImplementedError(f"Provider {self.name!r} does not support get_document")

    def get_parameters(self) -> dict[str, Any]:
        """Return provider metadata when available."""

        return {}

    def get_catalog(self) -> ProviderCatalog:
        """Return a normalized provider catalog when available."""

        return ProviderCatalog(source=self.name, raw=self.get_parameters())

    def get_capabilities(self) -> ProviderCapabilities:
        """Return declared source capabilities and extraction limits."""

        return ProviderCapabilities(
            source=self.name,
            display_name=self.name,
            source_url="",
            category="jurisprudence",
            access_statuses=[AccessStatus.PARTIAL],
            limitations=["Provider has not declared detailed capabilities yet."],
        )
