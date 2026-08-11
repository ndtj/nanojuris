"""High-level client for NanoJuris."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nanojuris.canonical import search_page_to_canonical
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import UnsupportedProviderError
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
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.providers.bnp_pangea import BnpPangeaProvider
from nanojuris.providers.cjf_jurisprudencia import CjfJurisprudenciaProvider
from nanojuris.providers.comunica_pje import ComunicaPjeProvider
from nanojuris.providers.eproc_jurisprudencia_federal import (
    TnuEprocJurisprudenciaProvider,
    Trf2EprocJurisprudenciaProvider,
    Trf6EprocJurisprudenciaProvider,
)
from nanojuris.providers.stf_informativo import StfInformativoProvider
from nanojuris.providers.stf_juris import StfJurisProvider
from nanojuris.providers.stj_informativo import StjInformativoProvider
from nanojuris.providers.stj_scon import StjSconProvider
from nanojuris.providers.stm_jurisprudencia import StmJurisprudenciaProvider
from nanojuris.providers.tce_sp_jurisprudencia import TceSpJurisprudenciaProvider
from nanojuris.providers.tcu_jurisprudencia import TcuJurisprudenciaProvider
from nanojuris.providers.tjac_cjsg import TjacCjsgProvider
from nanojuris.providers.tjac_esaj_cpopg import TjacEsajCpopgProvider
from nanojuris.providers.tjal_cjsg import TjalCjsgProvider
from nanojuris.providers.tjam_cjsg import TjamCjsgProvider
from nanojuris.providers.tjdf_juris import TjdfJurisProvider
from nanojuris.providers.tjgo_projudi_jurisprudencia import TjgoProjudiJurisprudenciaProvider
from nanojuris.providers.tjms_cjsg import TjmsCjsgProvider
from nanojuris.providers.tjpa_jurisprudencia_bff import TjpaJurisprudenciaBffProvider
from nanojuris.providers.tjpb_pje_jurisprudencia import TjpbPjeJurisprudenciaProvider
from nanojuris.providers.tjpi_juspi import TjpiJuspiProvider
from nanojuris.providers.tjrj_eproc_jurisprudencia import TjrjEprocJurisprudenciaProvider
from nanojuris.providers.tjrs_solr import TjrsSolrProvider
from nanojuris.providers.tjsc_eproc_jurisprudencia import TjscEprocJurisprudenciaProvider
from nanojuris.providers.tjsp_cjsg import TjspCjsgProvider
from nanojuris.providers.tjsp_eproc_jurisprudencia import TjspEprocJurisprudenciaProvider
from nanojuris.providers.tjsp_esaj_cpopg import TjspEsajCpopgProvider
from nanojuris.providers.tjsp_nugepnac import TjspNugepnacProvider
from nanojuris.providers.tre_sp_temas import TreSpTemasProvider
from nanojuris.providers.trf4_eproc_jurisprudencia import Trf4EprocJurisprudenciaProvider
from nanojuris.providers.trf5_jurisprudencia import Trf5JurisprudenciaProvider
from nanojuris.providers.tst_jurisprudencia import TstJurisprudenciaProvider
from nanojuris.routing import (
    JURISPRUDENCE_CATEGORIES,
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
                ComunicaPjeProvider(self.config),
                TnuEprocJurisprudenciaProvider(self.config),
                StfInformativoProvider(self.config),
                StfJurisProvider(self.config),
                StjInformativoProvider(self.config),
                StjSconProvider(self.config),
                StmJurisprudenciaProvider(self.config),
                TstJurisprudenciaProvider(self.config),
                TceSpJurisprudenciaProvider(self.config),
                TjacCjsgProvider(self.config),
                TjacEsajCpopgProvider(self.config),
                TjdfJurisProvider(self.config),
                TjgoProjudiJurisprudenciaProvider(self.config),
                TjalCjsgProvider(self.config),
                TjamCjsgProvider(self.config),
                TjmsCjsgProvider(self.config),
                TjpiJuspiProvider(self.config),
                TjrjEprocJurisprudenciaProvider(self.config),
                TjpaJurisprudenciaBffProvider(self.config),
                TjpbPjeJurisprudenciaProvider(self.config),
                TjspCjsgProvider(self.config),
                TjspEprocJurisprudenciaProvider(self.config),
                TjspEsajCpopgProvider(self.config),
                TjspNugepnacProvider(self.config),
                TreSpTemasProvider(self.config),
                TjrsSolrProvider(self.config),
                TjscEprocJurisprudenciaProvider(self.config),
                TcuJurisprudenciaProvider(self.config),
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
        return self._provider(source).search(query)

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

        selected_sources = list(sources) if sources is not None else self._default_unified_sources()
        capabilities = {item.source: item for item in self.list_sources()}
        routing = route_unified_sources(
            selected_sources=selected_sources,
            capabilities=capabilities,
            text=text,
            filters={
                "number": filters.get("number"),
                "party_name": filters.get("party_name") or filters.get("parte"),
                "party_document": filters.get("party_document"),
                "lawyer_name": filters.get("lawyer_name") or filters.get("advogado"),
                "oab": filters.get("oab"),
                "precatory_number": filters.get("precatory_number"),
                "police_document": filters.get("police_document"),
                "cda": filters.get("cda"),
            },
        )
        results: list[UnifiedSearchRecord] = []
        errors: list[dict[str, str]] = []
        for source in routing.searched:
            try:
                if canonical:
                    results.extend(
                        self.search_canonical(
                            text,
                            source=source,
                            courts=courts,
                            types=types,
                            page=page,
                            page_size=page_size,
                            **filters,
                        )
                    )
                else:
                    page_result = self.search(
                        text,
                        source=source,
                        courts=courts,
                        types=types,
                        page=page,
                        page_size=page_size,
                        **filters,
                    )
                    results.extend(page_result.results)
            except Exception as exc:
                if not continue_on_error:
                    raise
                errors.append(_source_error(source, exc))
        return {
            "sources": selected_sources,
            "searched_sources": routing.searched,
            "skipped_sources": [skip.to_dict() for skip in routing.skipped],
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
            "total_returned": len(results),
            "results": results,
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

    def _default_unified_sources(self) -> list[str]:
        return [
            capability.source
            for capability in self.list_sources()
            if capability.category in JURISPRUDENCE_CATEGORIES and capability.supports_mcp
        ]

    def _provider(self, source: str) -> JurisprudenceProvider:
        try:
            return self.providers[source]
        except KeyError as exc:
            available = ", ".join(sorted(self.providers))
            raise UnsupportedProviderError(
                f"Provider {source!r} is not registered. Available: {available}"
            ) from exc


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
