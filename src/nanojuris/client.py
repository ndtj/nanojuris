"""High-level client for NanoJuris."""

from __future__ import annotations

import re
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nanojuris.canonical import search_page_to_canonical
from nanojuris.collection import CollectionReport
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    InternalProviderError,
    InvalidQueryError,
    NanoJurisError,
    UnsupportedProviderError,
    UnsupportedQueryError,
)
from nanojuris.models import (
    CanonicalDecision,
    CanonicalDocument,
    CanonicalPrecedent,
    DecisionBundle,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    ProviderCatalog,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.providers.bnp_pangea import BnpPangeaProvider
from nanojuris.providers.cjf_jurisprudencia import CjfJurisprudenciaProvider
from nanojuris.providers.cnj_jurisprudencia import CnjJurisprudenciaProvider
from nanojuris.providers.eproc_jurisprudencia_federal import (
    TnuEprocJurisprudenciaProvider,
    Trf2EprocJurisprudenciaProvider,
    Trf6EprocJurisprudenciaProvider,
)
from nanojuris.providers.justica_eleitoral_sjur import JusticaEleitoralSjurProvider
from nanojuris.providers.stf_informativo import StfInformativoProvider
from nanojuris.providers.stf_juris import StfJurisProvider
from nanojuris.providers.stj_dados_abertos_jurisprudencia import StjDadosAbertosProvider
from nanojuris.providers.stj_informativo import StjInformativoProvider
from nanojuris.providers.stj_scon import StjSconProvider
from nanojuris.providers.stm_jurisprudencia import StmJurisprudenciaProvider
from nanojuris.providers.tce_sp_jurisprudencia import TceSpJurisprudenciaProvider
from nanojuris.providers.tcu_jurisprudencia import TcuJurisprudenciaProvider
from nanojuris.providers.tjac_cjsg import TjacCjsgProvider
from nanojuris.providers.tjal_cjsg import TjalCjsgProvider
from nanojuris.providers.tjam_cjsg import TjamCjsgProvider
from nanojuris.providers.tjba_graphql import TjbaGraphqlProvider
from nanojuris.providers.tjce_cjsg import TjceCjsgProvider
from nanojuris.providers.tjce_informativos import TjceInformativosProvider
from nanojuris.providers.tjce_sjuris import TjceSjurisProvider
from nanojuris.providers.tjdf_juris import TjdfJurisProvider
from nanojuris.providers.tjgo_projudi_jurisprudencia import TjgoProjudiJurisprudenciaProvider
from nanojuris.providers.tjma_jurisconsult import TjmaJurisconsultProvider
from nanojuris.providers.tjms_cjsg import TjmsCjsgProvider
from nanojuris.providers.tjmt_jurisprudencia_api import TjmtJurisprudenciaApiProvider
from nanojuris.providers.tjpa_jurisprudencia_bff import TjpaJurisprudenciaBffProvider
from nanojuris.providers.tjpb_pje_jurisprudencia import TjpbPjeJurisprudenciaProvider
from nanojuris.providers.tjpe_jurisprudencia import TjpeJurisprudenciaProvider
from nanojuris.providers.tjpi_juspi import TjpiJuspiProvider
from nanojuris.providers.tjpr_jurisprudencia import TjprJurisprudenciaProvider
from nanojuris.providers.tjrj_eproc_jurisprudencia import TjrjEprocJurisprudenciaProvider
from nanojuris.providers.tjro_liame import TjroLiameProvider
from nanojuris.providers.tjrr_juris import TjrrJurisProvider
from nanojuris.providers.tjrs_solr import TjrsSolrProvider
from nanojuris.providers.tjsc_eproc_jurisprudencia import TjscEprocJurisprudenciaProvider
from nanojuris.providers.tjsp_cjsg import TjspCjsgProvider
from nanojuris.providers.tjsp_eproc_jurisprudencia import TjspEprocJurisprudenciaProvider
from nanojuris.providers.tjsp_nugepnac import TjspNugepnacProvider
from nanojuris.providers.tjto_jurisprudencia import TjtoJurisprudenciaProvider
from nanojuris.providers.tre_sp_temas import TreSpTemasProvider
from nanojuris.providers.trf4_eproc_jurisprudencia import Trf4EprocJurisprudenciaProvider
from nanojuris.providers.trf5_jurisprudencia import Trf5JurisprudenciaProvider
from nanojuris.providers.tst_jurisprudencia import TstJurisprudenciaProvider
from nanojuris.routing import (
    JURISPRUDENCE_CATEGORIES,
    _unsupported_refinement_filters,
    build_routing_summary,
    route_unified_sources,
)
from nanojuris.source_contracts import (
    SourceContractAssessment,
    assess_source_contract,
    assess_source_contracts,
)
from nanojuris.store import ResearchRun, SQLiteStore

CanonicalSearchRecord = CanonicalDecision | CanonicalPrecedent
UnifiedSearchRecord = CanonicalSearchRecord | JurisprudenceResult


class NanoJurisClient:
    """Facade over public jurisprudence providers."""

    _KNOWN_FILTERS = {
        "all_words",
        "any_words",
        "without_words",
        "exact_phrase",
        "rapporteur",
        "updated_from",
        "updated_to",
        "published_from",
        "published_to",
        "include_cancelled",
        "order_by",
        "number",
        "party_name",
        "parte",
        "party_document",
        "lawyer_name",
        "advogado",
        "oab",
        "precatory_number",
        "police_document",
        "cda",
        "source_origin",
        "origin",
        "source_origins",
        "origins",
        "fetch_details",
    }

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        providers: Iterable[JurisprudenceProvider] | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        provider_list = (
            list(providers)
            if providers is not None
            else [
                BnpPangeaProvider(self.config),
                CjfJurisprudenciaProvider(self.config),
                CnjJurisprudenciaProvider(self.config),
                TnuEprocJurisprudenciaProvider(self.config),
                StfInformativoProvider(self.config),
                StfJurisProvider(self.config),
                StjInformativoProvider(self.config),
                StjDadosAbertosProvider(self.config),
                StjSconProvider(self.config),
                StmJurisprudenciaProvider(self.config),
                TstJurisprudenciaProvider(self.config),
                TceSpJurisprudenciaProvider(self.config),
                TjceInformativosProvider(self.config),
                TjacCjsgProvider(self.config),
                TjceCjsgProvider(self.config),
                TjceSjurisProvider(self.config),
                TjdfJurisProvider(self.config),
                TjgoProjudiJurisprudenciaProvider(self.config),
                TjalCjsgProvider(self.config),
                TjamCjsgProvider(self.config),
                TjmsCjsgProvider(self.config),
                TjmtJurisprudenciaApiProvider(self.config),
                TjmaJurisconsultProvider(self.config),
                TjbaGraphqlProvider(self.config),
                TjpiJuspiProvider(self.config),
                TjprJurisprudenciaProvider(self.config),
                TjrrJurisProvider(self.config),
                TjroLiameProvider(self.config),
                TjrjEprocJurisprudenciaProvider(self.config),
                TjpaJurisprudenciaBffProvider(self.config),
                TjpbPjeJurisprudenciaProvider(self.config),
                TjpeJurisprudenciaProvider(self.config),
                TjspCjsgProvider(self.config),
                TjspEprocJurisprudenciaProvider(self.config),
                TjspNugepnacProvider(self.config),
                TreSpTemasProvider(self.config),
                TjrsSolrProvider(self.config),
                TjscEprocJurisprudenciaProvider(self.config),
                TjtoJurisprudenciaProvider(self.config),
                TcuJurisprudenciaProvider(self.config),
                JusticaEleitoralSjurProvider(self.config),
                Trf5JurisprudenciaProvider(self.config),
                Trf2EprocJurisprudenciaProvider(self.config),
                Trf4EprocJurisprudenciaProvider(self.config),
                Trf6EprocJurisprudenciaProvider(self.config),
            ]
        )
        self.providers = {provider.name: provider for provider in provider_list}

    def search(
        self,
        text: str = "",
        *,
        source: str = "bnp_pangea",
        courts: list[str] | None = None,
        types: list[str] | None = None,
        page: int = 1,
        page_size: int = 10,
        **filters: Any,
    ) -> SearchPage:
        """Search one provider and return a normalized page."""

        unknown_filters = set(filters).difference(self._KNOWN_FILTERS)
        if unknown_filters:
            names = ", ".join(sorted(unknown_filters))
            raise InvalidQueryError(f"filtro(s) desconhecido(s): {names}")

        try:
            query = JurisprudenceQuery(
                text=text,
                courts=courts or [],
                types=types or [],
                page=page,
                page_size=page_size,
                all_words=str(filters.get("all_words") or ""),
                any_words=str(filters.get("any_words") or ""),
                without_words=str(filters.get("without_words") or ""),
                exact_phrase=str(filters.get("exact_phrase") or ""),
                rapporteur=str(filters.get("rapporteur") or ""),
                updated_from=str(filters.get("updated_from") or ""),
                updated_to=str(filters.get("updated_to") or ""),
                published_from=str(filters.get("published_from") or ""),
                published_to=str(filters.get("published_to") or ""),
                include_cancelled=bool(filters.get("include_cancelled") or False),
                order_by=str(filters.get("order_by") or "Text"),
                number=str(filters.get("number") or ""),
                party_name=str(filters.get("party_name") or filters.get("parte") or ""),
                party_document=str(filters.get("party_document") or ""),
                lawyer_name=str(filters.get("lawyer_name") or filters.get("advogado") or ""),
                oab=str(filters.get("oab") or ""),
                precatory_number=str(filters.get("precatory_number") or ""),
                police_document=str(filters.get("police_document") or ""),
                cda=str(filters.get("cda") or ""),
                source_origin=str(filters.get("source_origin") or filters.get("origin") or ""),
                source_origins=list(filters.get("source_origins") or filters.get("origins") or []),
                fetch_details=bool(filters.get("fetch_details") or False),
            )
        except ValueError as exc:
            raise InvalidQueryError(str(exc)) from exc
        provider = self._provider(source)
        search_page = provider.search(query)
        unsupported = _unsupported_refinement_filters(
            provider.get_capabilities(),
            text=text,
            filters={
                "courts": query.courts,
                "types": query.types,
                "exact_phrase": query.exact_phrase,
                "all_words": query.all_words,
                "any_words": query.any_words,
                "without_words": query.without_words,
                "rapporteur": query.rapporteur,
                "published_from": query.published_from,
                "published_to": query.published_to,
                "updated_from": query.updated_from,
                "updated_to": query.updated_to,
                "source_origin": query.source_origin,
                "source_origins": query.source_origins,
                "fetch_details": query.fetch_details,
            },
        )
        if unsupported:
            trace = search_page.source_trace or SourceTrace(
                provider=source,
                endpoint="search",
            )
            trace.limitations.extend(
                f"Filtro nao suportado pela declaracao do provider: {name}."
                for name in sorted(unsupported)
            )
            search_page.source_trace = trace
        return search_page

    def search_canonical(
        self,
        text: str = "",
        *,
        source: str = "bnp_pangea",
        courts: list[str] | None = None,
        types: list[str] | None = None,
        page: int = 1,
        page_size: int = 10,
        **filters: Any,
    ) -> list[CanonicalSearchRecord]:
        """Search one provider and return canonical extraction records."""

        search_page = self.search(
            text,
            source=source,
            courts=courts,
            types=types,
            page=page,
            page_size=page_size,
            **filters,
        )
        return search_page_to_canonical(search_page)

    def collect(
        self,
        query: JurisprudenceQuery,
        *,
        source: str = "bnp_pangea",
        store: SQLiteStore | None = None,
        checkpoint_path: str | Path | None = None,
        max_pages: int = 100,
        max_records: int = 10_000,
        resume: bool = True,
        clear_checkpoint_on_complete: bool = False,
    ) -> CollectionReport:
        """Collect one source with canonicalization, deduplication and checkpointing."""

        from nanojuris.collection import CollectionRunner

        provider = self._provider(source)
        return CollectionRunner(
            provider,
            store=store,
            checkpoint_path=checkpoint_path,
            max_pages=max_pages,
            max_records=max_records,
        ).collect(
            query,
            resume=resume,
            clear_checkpoint_on_complete=clear_checkpoint_on_complete,
        )

    def search_many(
        self,
        text: str = "",
        *,
        sources: list[str] | None = None,
        courts: list[str] | None = None,
        types: list[str] | None = None,
        page: int = 1,
        page_size: int = 10,
        canonical: bool = True,
        continue_on_error: bool = True,
        **filters: Any,
    ) -> dict[str, Any]:
        """Search multiple jurisprudence sources and return one aggregated payload."""

        unknown_filters = set(filters).difference(self._KNOWN_FILTERS)
        if unknown_filters:
            names = ", ".join(sorted(unknown_filters))
            raise InvalidQueryError(f"filtro(s) desconhecido(s): {names}")
        try:
            JurisprudenceQuery(
                page=page,
                page_size=page_size,
                updated_from=str(filters.get("updated_from") or ""),
                updated_to=str(filters.get("updated_to") or ""),
                published_from=str(filters.get("published_from") or ""),
                published_to=str(filters.get("published_to") or ""),
            )
        except ValueError as exc:
            raise InvalidQueryError(str(exc)) from exc

        selected_sources = list(sources) if sources is not None else self._default_unified_sources()
        capabilities = {item.source: item for item in self.list_sources()}
        routing = route_unified_sources(
            selected_sources=selected_sources,
            capabilities=capabilities,
            text=text,
            filters={
                "courts": courts,
                "types": types,
                "number": filters.get("number"),
                "party_name": filters.get("party_name") or filters.get("parte"),
                "party_document": filters.get("party_document"),
                "lawyer_name": filters.get("lawyer_name") or filters.get("advogado"),
                "oab": filters.get("oab"),
                "precatory_number": filters.get("precatory_number"),
                "police_document": filters.get("police_document"),
                "cda": filters.get("cda"),
                "rapporteur": filters.get("rapporteur"),
                "exact_phrase": filters.get("exact_phrase"),
                "all_words": filters.get("all_words"),
                "any_words": filters.get("any_words"),
                "without_words": filters.get("without_words"),
                "published_from": filters.get("published_from"),
                "published_to": filters.get("published_to"),
                "updated_from": filters.get("updated_from"),
                "updated_to": filters.get("updated_to"),
                "source_origin": filters.get("source_origin") or filters.get("origin"),
                "source_origins": filters.get("source_origins") or filters.get("origins"),
                "fetch_details": filters.get("fetch_details"),
            },
        )
        results: list[UnifiedSearchRecord] = []
        errors: list[dict[str, str]] = []
        source_totals: dict[str, int] = {}
        source_completeness: dict[str, dict[str, Any]] = {}

        def fetch_source(
            source: str,
        ) -> tuple[list[UnifiedSearchRecord], int, SearchPage, int]:
            records: list[UnifiedSearchRecord] = []
            source_page = 1
            pages_fetched = 0
            page_result: SearchPage | None = None
            target = page * page_size
            source_page_size = min(100, target)
            while len(records) < target:
                page_result = self.search(
                    text,
                    source=source,
                    courts=courts,
                    types=types,
                    page=source_page,
                    page_size=source_page_size,
                    **filters,
                )
                pages_fetched += 1
                if canonical:
                    page_records: list[UnifiedSearchRecord] = list(
                        search_page_to_canonical(page_result)
                    )
                else:
                    page_records = list(page_result.results)
                if not page_records:
                    break
                records.extend(page_records)
                if page_result.is_complete is True:
                    break
                if page_result.total >= 0 and len(records) >= page_result.total:
                    break
                source_page += 1
            if page_result is None:
                raise InternalProviderError(f"provider {source} returned no search page")
            return records, page_result.total, page_result, pages_fetched

        executor = ThreadPoolExecutor(
            max_workers=max(1, min(self.config.unified_max_workers, len(routing.searched)))
        )
        futures = {source: executor.submit(fetch_source, source) for source in routing.searched}
        done, pending = wait(futures.values(), timeout=self.config.unified_timeout)
        for source in routing.searched:
            future = futures[source]
            if future in pending:
                error = TimeoutError(
                    f"tempo limite global da busca unificada excedido para {source}"
                )
                if not continue_on_error:
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise error
                errors.append(_source_error(source, error))
                continue
            try:
                source_results, total, page_result, pages_fetched = future.result()
                source_totals[source] = total
                source_completeness[source] = {
                    "returned": len(source_results),
                    "reported_total": total,
                    "pagination_mode": page_result.pagination_mode,
                    "complete": page_result.is_complete,
                    "reason": page_result.completeness_reason,
                    "pages_fetched": pages_fetched,
                }
                results.extend(source_results)
            except Exception as exc:
                if not continue_on_error:
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise
                if not isinstance(exc, NanoJurisError) and _classify_error(exc).error_type not in {
                    "NetworkConfigurationError",
                    "SslVerificationError",
                }:
                    exc = InternalProviderError(
                        f"provider {source} failed with an unexpected internal error"
                    )
                errors.append(_source_error(source, exc))
                source_completeness[source] = {
                    "returned": 0,
                    "reported_total": None,
                    "pagination_mode": "failed",
                    "complete": False,
                    "reason": "A fonte nao concluiu a consulta.",
                    "pages_fetched": 0,
                }
        executor.shutdown(wait=False, cancel_futures=True)

        results = _rank_and_deduplicate(results, text=text)
        offset = (page - 1) * page_size
        paged_results = results[offset : offset + page_size]
        sources_complete = [
            source for source, status in source_completeness.items() if status["complete"] is True
        ]
        sources_partial = [
            source for source, status in source_completeness.items() if status["complete"] is False
        ]
        sources_unknown = [
            source for source, status in source_completeness.items() if status["complete"] is None
        ]
        collection_complete = (
            bool(routing.searched)
            and not routing.skipped
            and not routing.warnings
            and not errors
            and not (sources_partial or sources_unknown)
        )
        observed_total_pages = (len(results) + page_size - 1) // page_size if page_size else 0
        page_end = offset + len(paged_results)
        # A partial collection is not proof that another federated page can be
        # materialized safely. Only expose a next page when the current
        # in-memory collection actually contains one.
        has_more = page_end < len(results)
        return {
            "sources": selected_sources,
            "searched_sources": routing.searched,
            "skipped_sources": [skip.to_dict() for skip in routing.skipped],
            "routing_warnings": [warning.to_dict() for warning in routing.warnings],
            "routing_summary": [
                item.to_dict()
                for item in build_routing_summary(
                    routed=routing,
                    capabilities=capabilities,
                    errors=errors,
                )
            ],
            "page": page,
            "page_size": page_size,
            "canonical": canonical,
            "total_available": len(results),
            "total_returned": len(paged_results),
            "deduplicated_total": len(results),
            "observed_total_pages": observed_total_pages,
            "has_more": has_more,
            "next_page": page + 1 if has_more else None,
            "previous_page": page - 1 if page > 1 else None,
            "pagination_complete": collection_complete,
            "source_totals": source_totals,
            "source_completeness": source_completeness,
            "sources_complete": sources_complete,
            "sources_partial": sources_partial,
            "sources_unknown": sources_unknown,
            "collection_complete": collection_complete,
            "completeness_reason": (
                "Todas as fontes declararam a janela coletada como completa."
                if collection_complete
                else "A resposta representa uma coleta parcial, desconhecida ou com falhas; "
                "consulte routing_warnings, source_completeness e errors."
            ),
            "federated": True,
            # Kept for server-side snapshot consumers. Public adapters should
            # continue returning only the requested page.
            "collected_results": results,
            "results": paged_results,
            "errors": errors,
        }

    def search_and_store(
        self,
        text: str = "",
        *,
        store: SQLiteStore | str | Path,
        source: str = "bnp_pangea",
        courts: list[str] | None = None,
        types: list[str] | None = None,
        page: int = 1,
        page_size: int = 10,
        **filters: Any,
    ) -> list[CanonicalSearchRecord]:
        """Search one provider, canonicalize results and persist them."""

        records = self.search_canonical(
            text,
            source=source,
            courts=courts,
            types=types,
            page=page,
            page_size=page_size,
            **filters,
        )
        if isinstance(store, SQLiteStore):
            store.save_many(records)
            return records
        with SQLiteStore(store) as sqlite_store:
            sqlite_store.save_many(records)
        return records

    def search_and_store_run(
        self,
        text: str = "",
        *,
        store: SQLiteStore | str | Path,
        source: str = "bnp_pangea",
        courts: list[str] | None = None,
        types: list[str] | None = None,
        page: int = 1,
        page_size: int = 10,
        label: str | None = None,
        **filters: Any,
    ) -> ResearchRun:
        """Search one provider, persist results and return a saved search run."""

        records = self.search_canonical(
            text,
            source=source,
            courts=courts,
            types=types,
            page=page,
            page_size=page_size,
            **filters,
        )
        query = {
            "text": text,
            "source": source,
            "courts": courts or [],
            "types": types or [],
            "page": page,
            "page_size": page_size,
            **filters,
        }
        if isinstance(store, SQLiteStore):
            return store.save_research_run(
                source=source,
                text=text,
                query=query,
                records=records,
                label=label,
            )
        with SQLiteStore(store) as sqlite_store:
            return sqlite_store.save_research_run(
                source=source,
                text=text,
                query=query,
                records=records,
                label=label,
            )

    def search_many_and_store_run(
        self,
        text: str = "",
        *,
        store: SQLiteStore | str | Path,
        sources: list[str] | None = None,
        courts: list[str] | None = None,
        types: list[str] | None = None,
        page: int = 1,
        page_size: int = 10,
        label: str | None = None,
        **filters: Any,
    ) -> ResearchRun:
        """Persist one reproducible federated search run.

        The saved query retains source-level completeness and errors so a run
        cannot be interpreted as a complete national collection by accident.
        Only the canonical records returned in the requested page are stored.
        """

        payload = self.search_many(
            text,
            sources=sources,
            courts=courts,
            types=types,
            page=page,
            page_size=page_size,
            canonical=True,
            **filters,
        )
        query = {
            "text": text,
            "sources": payload["sources"],
            "searched_sources": payload["searched_sources"],
            "skipped_sources": payload["skipped_sources"],
            "courts": courts or [],
            "types": types or [],
            "page": page,
            "page_size": page_size,
            "total_available": payload["total_available"],
            "total_returned": payload["total_returned"],
            "deduplicated_total": payload["deduplicated_total"],
            "source_totals": payload["source_totals"],
            "source_completeness": payload["source_completeness"],
            "sources_complete": payload["sources_complete"],
            "sources_partial": payload["sources_partial"],
            "sources_unknown": payload["sources_unknown"],
            "collection_complete": payload["collection_complete"],
            "completeness_reason": payload["completeness_reason"],
            "errors": payload["errors"],
            **filters,
        }
        records = [
            record
            for record in payload["results"]
            if isinstance(record, (CanonicalDecision, CanonicalPrecedent))
        ]
        if isinstance(store, SQLiteStore):
            return store.save_research_run(
                source="federated",
                text=text,
                query=query,
                records=records,
                label=label,
            )
        with SQLiteStore(store) as sqlite_store:
            return sqlite_store.save_research_run(
                source="federated",
                text=text,
                query=query,
                records=records,
                label=label,
            )

    def get_decisions(self, precedent_id: str, *, source: str = "bnp_pangea") -> DecisionBundle:
        """Return decisions linked to a precedent."""

        return self._provider(source).get_decisions(precedent_id)

    def get_document(self, document_id: str, *, source: str = "tjsp_cjsg") -> CanonicalDocument:
        """Return one public source document as a canonical document."""

        return self._provider(source).get_document(document_id)

    def get_parameters(self, *, source: str = "bnp_pangea") -> dict[str, Any]:
        """Return provider metadata."""

        return self._provider(source).get_parameters()

    def get_catalog(self, *, source: str = "bnp_pangea") -> ProviderCatalog:
        """Return a normalized provider catalog."""

        return self._provider(source).get_catalog()

    def list_source_datasets(
        self,
        *,
        source: str,
        query: str = "jurisprudencia",
        rows: int = 20,
    ) -> list[dict[str, Any]]:
        """List datasets when a provider exposes a public dataset catalog."""

        provider = self._provider(source)
        method = getattr(provider, "list_source_datasets", None)
        if not callable(method):
            raise UnsupportedQueryError(f"Provider {source!r} does not expose a dataset catalog")
        return method(query=query, rows=rows)

    def describe_source_dataset(self, *, source: str, dataset_id: str) -> dict[str, Any]:
        """Describe one public dataset without downloading its resources."""

        provider = self._provider(source)
        method = getattr(provider, "describe_dataset", None)
        if not callable(method):
            raise UnsupportedQueryError(f"Provider {source!r} does not describe datasets")
        return method(dataset_id)

    def plan_source_sync(
        self,
        *,
        source: str,
        dataset_id: str,
        format: str = "JSON",
        max_resources: int = 100,
    ) -> dict[str, Any]:
        """Plan a dataset sync without downloading any resource."""

        provider = self._provider(source)
        method = getattr(provider, "plan_source_sync", None)
        if not callable(method):
            raise UnsupportedQueryError(f"Provider {source!r} does not plan dataset syncs")
        return method(dataset_id, format=format, max_resources=max_resources)

    def sync_source_resource(
        self,
        *,
        source: str,
        dataset_id: str,
        resource_id: str,
        store: SQLiteStore,
        max_bytes: int = 50_000_000,
        label: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Synchronize one explicit provider resource into a local store."""

        provider = self._provider(source)
        method = getattr(provider, "sync_resource", None)
        if not callable(method):
            raise UnsupportedQueryError(f"Provider {source!r} does not sync resources")
        result = method(
            dataset_id,
            resource_id,
            store=store,
            max_bytes=max_bytes,
            label=label,
            force=force,
        )
        if hasattr(result, "to_dict"):
            return result.to_dict()
        return result

    def get_capabilities(self, *, source: str = "bnp_pangea") -> ProviderCapabilities:
        """Return declared capabilities and limits for one provider."""

        return self._provider(source).get_capabilities()

    def list_sources(self) -> list[ProviderCapabilities]:
        """Return declared capabilities for all registered providers."""

        return [self.providers[name].get_capabilities() for name in sorted(self.providers)]

    def get_source_contract(self, *, source: str) -> SourceContractAssessment:
        """Return a maturity assessment for one provider contract."""

        return assess_source_contract(self.get_capabilities(source=source))

    def list_source_contracts(self) -> list[SourceContractAssessment]:
        """Return maturity assessments for all registered provider contracts."""

        return assess_source_contracts(self.list_sources())

    def list_suggestions(self, text: str, *, source: str = "bnp_pangea") -> list[str]:
        """Return provider search suggestions when supported."""

        provider = self._provider(source)
        if hasattr(provider, "list_suggestions"):
            suggestions = provider.list_suggestions(text)  # type: ignore[attr-defined]
            return list(suggestions)
        return []

    def validate_sources(
        self,
        *,
        sources: list[str] | None = None,
        text: str = "responsabilidade civil",
        page_size: int = 1,
        timeout: float | None = None,
        max_workers: int | None = None,
    ) -> dict[str, Any]:
        """Run the bounded live contract check shared by CLI, MCP and Studio."""

        from nanojuris.validation import validate_sources

        return validate_sources(
            self,
            sources=sources,
            text=text,
            page_size=page_size,
            timeout=timeout,
            max_workers=max_workers,
        )

    def _default_unified_sources(self) -> list[str]:
        return [
            capability.source
            for capability in self.list_sources()
            if capability.category in JURISPRUDENCE_CATEGORIES
            and capability.supports_unified_search
        ]

    def _provider(self, source: str) -> JurisprudenceProvider:
        try:
            return self.providers[source]
        except KeyError as exc:
            available = ", ".join(sorted(self.providers))
            raise UnsupportedProviderError(
                f"Provider {source!r} is not registered. Available: {available}"
            ) from exc


def _rank_and_deduplicate(
    results: list[UnifiedSearchRecord],
    *,
    text: str,
) -> list[UnifiedSearchRecord]:
    """Create a deterministic federated order and remove repeated legal records."""

    unique: dict[str, tuple[int, UnifiedSearchRecord]] = {}
    tokens = [token for token in re.findall(r"\w+", text.lower()) if len(token) > 2]
    for record in results:
        identity = _record_identity(record)
        haystack = " ".join(
            str(getattr(record, field, "") or "")
            for field in ("question", "thesis", "summary", "case_number", "number")
        ).lower()
        score = sum(haystack.count(token) for token in tokens)
        previous = unique.get(identity)
        if previous is None or score > previous[0]:
            unique[identity] = (score, record)
    ranked = list(unique.values())
    ranked.sort(key=lambda item: (-item[0], item[1].source, item[1].id))
    return [record for _, record in ranked]


def _record_identity(record: UnifiedSearchRecord) -> str:
    case_number = getattr(record, "case_number", None) or getattr(record, "number", None)
    if case_number:
        return f"case:{re.sub(r'[^0-9a-z]', '', str(case_number).lower())}"
    if isinstance(record, CanonicalPrecedent):
        return f"precedent:{record.court}:{record.precedent_type}:{record.number or record.id}"
    return f"source:{record.source}:{record.id}"


@dataclass(frozen=True, slots=True)
class _ErrorClassification:
    error_type: str
    message: str
    hint: str


def _source_error(source: str, exc: Exception) -> dict[str, str]:
    classified = _classify_error(exc)
    payload = {
        "source": source,
        "error_type": classified.error_type,
        "message": classified.message,
    }
    if classified.hint:
        payload["hint"] = classified.hint
    return payload


def _classify_error(exc: Exception) -> _ErrorClassification:
    chain_text = " | ".join(str(item) for item in _exception_chain(exc))
    lowered = chain_text.lower()
    if "proxyerror" in lowered or "unable to connect to proxy" in lowered:
        return _ErrorClassification(
            error_type="NetworkConfigurationError",
            message=(
                "A configuracao local de proxy impediu a conexao com a fonte publica. "
                "A busca foi roteada corretamente, mas nao conseguiu acessar a internet."
            ),
            hint=(
                "Verifique HTTP_PROXY, HTTPS_PROXY, ALL_PROXY ou rode o Studio com "
                "--ignore-env-proxy quando o proxy local estiver invalido."
            ),
        )
    if "ssl" in lowered and ("certificate" in lowered or "certificado" in lowered):
        return _ErrorClassification(
            error_type="SslVerificationError",
            message=(
                "A verificacao SSL local impediu a conexao com a fonte publica. "
                "Isso costuma indicar cadeia de certificados ausente ou interceptacao corporativa."
            ),
            hint=(
                "Atualize os certificados do ambiente. Para diagnostico controlado, use "
                "--sem-verificar-ssl apenas em probe-rota."
            ),
        )
    return _ErrorClassification(
        error_type=type(exc).__name__,
        message=str(exc),
        hint="",
    )


def _exception_chain(exc: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        chain.append(current)
        seen.add(id(current))
        current = current.__cause__ or current.__context__
    return chain
