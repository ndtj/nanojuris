"""Provider contract for jurisprudence sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import replace
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

    def iter_pages(
        self,
        query: JurisprudenceQuery,
        *,
        max_records: int | None = None,
    ) -> Iterator[SearchPage]:
        """Yield deduplicated pages using the provider's public page contract.

        Providers with a source-specific pagination mechanism may override this
        method. The default keeps a single stable contract for page-based
        sources and stops conservatively when no new identifiers are returned.
        """

        if max_records is not None and max_records < 1:
            raise ValueError("max_records deve ser maior que zero")
        target = max_records if max_records is not None else float("inf")
        seen: set[str] = set()
        page_number = query.page
        max_page = self.get_capabilities().max_remote_page
        while max_page is None or page_number <= max_page:
            page = self.search(replace(query, page=page_number))
            unique_results = [result for result in page.results if result.id not in seen]
            duplicate_results = len(unique_results) != len(page.results)
            stalled = bool(page.results) and not unique_results
            remaining = None if target == float("inf") else int(target - len(seen))
            target_truncated = remaining is not None and len(unique_results) > remaining
            if target_truncated:
                unique_results = unique_results[:remaining]
            seen.update(result.id for result in unique_results)
            if duplicate_results or target_truncated:
                reason_parts = []
                if duplicate_results:
                    reason_parts.append("a pagina foi deduplicada localmente")
                if stalled:
                    reason_parts.append("a fonte repetiu uma pagina sem novos identificadores")
                if target_truncated:
                    reason_parts.append("a pagina foi limitada por max_records")
                page = replace(
                    page,
                    results=unique_results,
                    end=page.start + len(unique_results) - 1 if unique_results else 0,
                    is_complete=False,
                    completeness_reason="; ".join(reason_parts) + ".",
                )
            yield page
            if not page.results or len(seen) >= target:
                break
            if stalled:
                break
            if page.is_complete is True or (page.total > 0 and len(seen) >= page.total):
                break
            page_number += 1

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
