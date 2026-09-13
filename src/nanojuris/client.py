"""High-level client for NanoJuris."""

from __future__ import annotations

import re
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from nanojuris.adaptive_search import SearchPlan, plan_live_search
from nanojuris.canonical import search_page_to_canonical
from nanojuris.collection import CollectionReport
from nanojuris.config import NanoJurisConfig
from nanojuris.contracts import (
    SearchOutcomeStatus,
    search_outcome_from_error,
    search_outcome_from_page,
)
from nanojuris.errors import (
    AccessControlRequiredError,
    InternalProviderError,
    InvalidQueryError,
    NanoJurisError,
    ParserContractChangedError,
    SourceUnavailableError,
    UnsupportedProviderError,
    UnsupportedQueryError,
    safe_error_message,
)
from nanojuris.identity import identity_key
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
from nanojuris.normalization import normalize_date_value
from nanojuris.pagination import authoritative_total_reached
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.providers.bnp_pangea import BnpPangeaProvider
from nanojuris.providers.cjf_jurisprudencia import CjfJurisprudenciaProvider
from nanojuris.providers.cnj_jurisprudencia import CnjJurisprudenciaProvider
from nanojuris.providers.eproc_jurisprudencia_federal import (
    FederalEprocJurisprudenciaFamilyProvider,
)
from nanojuris.providers.falcao_jt import FalcaoJtProvider
from nanojuris.providers.justica_eleitoral_sjur import JusticaEleitoralSjurProvider
from nanojuris.providers.stf_informativo import StfInformativoProvider
from nanojuris.providers.stf_juris import StfJurisProvider
from nanojuris.providers.stj_dados_abertos_jurisprudencia import StjDadosAbertosProvider
from nanojuris.providers.stj_informativo import StjInformativoProvider
from nanojuris.providers.stj_scon import StjSconProvider
from nanojuris.providers.stm_jurisprudencia import StmJurisprudenciaProvider
from nanojuris.providers.tce_pr_viajuris import TcePrViaJurisProvider
from nanojuris.providers.tce_sp_jurisprudencia import TceSpJurisprudenciaProvider
from nanojuris.providers.tcu_jurisprudencia import TcuJurisprudenciaProvider
from nanojuris.providers.tjac_banco_sentencas import TjacBancoSentencasProvider
from nanojuris.providers.tjac_cjsg import TjacCjsgProvider
from nanojuris.providers.tjac_ementario_jurisprudencia import (
    TjacEmentarioJurisprudenciaProvider,
)
from nanojuris.providers.tjal_cjsg import TjalCjsgProvider
from nanojuris.providers.tjal_esmal_banco_sentencas import (
    TjalEsmalBancoSentencasProvider,
)
from nanojuris.providers.tjal_turma_recursal_ementario import (
    TjalTurmaRecursalEmentarioProvider,
)
from nanojuris.providers.tjam_cjsg import TjamCjsgProvider
from nanojuris.providers.tjap_banco_sentencas import TjapBancoSentencasProvider
from nanojuris.providers.tjap_tucujuris import TjapTucujurisProvider
from nanojuris.providers.tjba_graphql import TjbaGraphqlProvider
from nanojuris.providers.tjce_cjsg import TjceCjsgProvider
from nanojuris.providers.tjce_informativos import TjceInformativosProvider
from nanojuris.providers.tjce_sjuris import TjceSjurisProvider
from nanojuris.providers.tjdf_juris import TjdfJurisProvider
from nanojuris.providers.tjes_cjpg import TjesCjpgProvider
from nanojuris.providers.tjes_jurisprudencia import TjesJurisprudenciaProvider
from nanojuris.providers.tjes_turma_recursal import TjesTurmaRecursalProvider
from nanojuris.providers.tjgo_projudi_jurisprudencia import TjgoProjudiJurisprudenciaProvider
from nanojuris.providers.tjma_informativos import TjmaInformativosProvider
from nanojuris.providers.tjma_jurisconsult import TjmaJurisconsultProvider
from nanojuris.providers.tjmg_dspace_jurisprudencia import (
    TjmgDspaceJurisprudenciaProvider,
)
from nanojuris.providers.tjmg_ejef_boletim_jurisprudencia import (
    TjmgEjefBoletimJurisprudenciaProvider,
)
from nanojuris.providers.tjmg_jurisprudencia import TjmgJurisprudenciaProvider
from nanojuris.providers.tjmmg_jurisprudencia_api import TjmmgJurisprudenciaApiProvider
from nanojuris.providers.tjmrs_jurisprudencia import TjmrsJurisprudenciaProvider
from nanojuris.providers.tjms_cjpg import TjmsCjpgProvider
from nanojuris.providers.tjms_cjsg import TjmsCjsgProvider
from nanojuris.providers.tjmsp_jurisprudencia import TjmspJurisprudenciaProvider
from nanojuris.providers.tjmt_jurisprudencia_api import TjmtJurisprudenciaApiProvider
from nanojuris.providers.tjpa_jurisprudencia_bff import TjpaJurisprudenciaBffProvider
from nanojuris.providers.tjpb_pje_jurisprudencia import TjpbPjeJurisprudenciaProvider
from nanojuris.providers.tjpe_jurisprudencia import TjpeJurisprudenciaProvider
from nanojuris.providers.tjpi_juspi import TjpiJuspiProvider
from nanojuris.providers.tjpr_jurisprudencia import TjprJurisprudenciaProvider
from nanojuris.providers.tjrj_banco_sentencas import TjrjBancoSentencasProvider
from nanojuris.providers.tjrj_ejuris import TjrjEjurisProvider
from nanojuris.providers.tjrj_eproc_jurisprudencia import TjrjEprocJurisprudenciaProvider
from nanojuris.providers.tjrn_jurisprudencia import TjrnJurisprudenciaProvider
from nanojuris.providers.tjro_jurisprudencia import TjroJurisprudenciaProvider
from nanojuris.providers.tjro_liame import TjroLiameProvider
from nanojuris.providers.tjrr_juris import TjrrJurisProvider
from nanojuris.providers.tjrs_solr import TjrsSolrProvider
from nanojuris.providers.tjsc_eproc_jurisprudencia import TjscEprocJurisprudenciaProvider
from nanojuris.providers.tjse_boletim_jurisprudencia import (
    TjseBoletimJurisprudenciaProvider,
)
from nanojuris.providers.tjse_jurisprudencia import TjseJurisprudenciaProvider
from nanojuris.providers.tjsp_cjpg import TjspCjpgProvider
from nanojuris.providers.tjsp_cjsg import TjspCjsgProvider
from nanojuris.providers.tjsp_eproc_jurisprudencia import TjspEprocJurisprudenciaProvider
from nanojuris.providers.tjsp_nugepnac import TjspNugepnacProvider
from nanojuris.providers.tjto_jurisprudencia import TjtoJurisprudenciaProvider
from nanojuris.providers.tnu_eproc_jurisprudencia import TnuEprocJurisprudenciaProvider
from nanojuris.providers.tre_sjur_first_degree import (
    TreSjurFirstDegreeFamilyProvider,
    TreSjurFirstDegreeProvider,
)
from nanojuris.providers.tre_sp_temas import TreSpTemasProvider
from nanojuris.providers.trf2_eproc_jurisprudencia import Trf2EprocJurisprudenciaProvider
from nanojuris.providers.trf3_jurisprudencia import Trf3JurisprudenciaProvider
from nanojuris.providers.trf4_eproc_jurisprudencia import Trf4EprocJurisprudenciaProvider
from nanojuris.providers.trf5_jurisprudencia import Trf5JurisprudenciaProvider
from nanojuris.providers.trf6_eproc_jurisprudencia import Trf6EprocJurisprudenciaProvider
from nanojuris.providers.trt2_basis_jurisprudencia import Trt2BasisJurisprudenciaProvider
from nanojuris.providers.trt2_ementario_jurisprudencia import (
    Trt2EmentarioJurisprudenciaProvider,
)
from nanojuris.providers.trt2_pje_jurisprudencia import Trt2PjeJurisprudenciaProvider
from nanojuris.providers.trt3_ementario_jurisprudencia import (
    Trt3EmentarioJurisprudenciaProvider,
)
from nanojuris.providers.trt4_sumulas_jurisprudencia import (
    Trt4SumulasJurisprudenciaProvider,
)
from nanojuris.providers.trt6_jurisprudencia import Trt6JurisprudenciaProvider
from nanojuris.providers.trt8_pje_jurisprudencia import Trt8PjeJurisprudenciaProvider
from nanojuris.providers.trt9_nugepnac_jurisprudencia import (
    Trt9NugepnacJurisprudenciaProvider,
)
from nanojuris.providers.trt15_jurisprudencia import Trt15JurisprudenciaProvider
from nanojuris.providers.tse_sjur_jurisprudencia import (
    TRE_AUTHORITIES,
    TreSjurJurisprudenciaFamilyProvider,
    TreSjurJurisprudenciaProvider,
    TseSjurJurisprudenciaProvider,
)
from nanojuris.providers.tst_jurisprudencia import TstJurisprudenciaProvider
from nanojuris.relevance import BM25_VERSION, RANKING_VERSION, LegalLiveRanker
from nanojuris.routing import (
    JURISPRUDENCE_CATEGORIES,
    _identifier_filters,
    _unsupported_refinement_filters,
    build_routing_summary,
    build_source_outcomes,
    route_unified_sources,
)
from nanojuris.search_intent import LegalQueryAnalyzer
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
        "judgment_date_from",
        "judgment_date_to",
        "judgment_from",
        "judgment_to",
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
        # Canonical legal dimensions (Portuguese aliases are retained for
        # callers integrating existing court terminology).
        "case_class",
        "classe",
        "judging_body",
        "orgao_julgador",
        "degree",
        "grau",
        "instance",
        "instancia",
        "branch",
        "ramo",
        "legal_area",
        "area_juridica",
        "authority",
        "autoridade",
        "collection",
        "colecao",
        "document_type",
        "tipo_documento",
        "decision_type",
        "tipo_decisao",
        # Official SJUR/TRE structured refinements.  Keep both canonical
        # English names and the Portuguese aliases accepted by the public
        # facade so Studio/federation do not reject fields that the TRE
        # contract can translate natively.
        "election_year",
        "ano_eleicao",
        "observations",
        "observacoes",
        "tags",
        "etiquetas",
        "municipality",
        "municipio",
        "publication_source",
        "fonte_publicacao",
        "publication_number",
        "numero_publicacao",
        "publication_volume",
        "volume_publicacao",
        "uf",
        "ignored_intent_filters",
    }

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        providers: Iterable[JurisprudenceProvider] | None = None,
        *,
        include_candidate_providers: bool = False,
    ) -> None:
        self.config = config or NanoJurisConfig()
        if providers is not None:
            provider_list = list(providers)
        else:
            provider_list = [
                BnpPangeaProvider(self.config),
                CjfJurisprudenciaProvider(self.config),
                CnjJurisprudenciaProvider(self.config),
                # The federal eproc dispatcher is an explicit-authority
                # runtime binding.  Its concrete installations remain
                # independently validated and the family stays opt-in (no
                # aggregate search or default federation).
                FederalEprocJurisprudenciaFamilyProvider(self.config),
                TnuEprocJurisprudenciaProvider(self.config),
                StfInformativoProvider(self.config),
                StfJurisProvider(self.config),
                StjInformativoProvider(self.config),
                StjDadosAbertosProvider(self.config),
                StjSconProvider(self.config),
                StmJurisprudenciaProvider(self.config),
                TstJurisprudenciaProvider(self.config),
                # The official SJUR/TRE family has a bounded textual contract
                # for every regional electoral court.  Keep the family
                # discoverable in the normal runtime so callers can select a
                # TRE explicitly; its capability remains opt-in because the
                # source has not proved remote pagination for all UFs.
                TreSjurJurisprudenciaFamilyProvider(self.config),
                # First-degree SJUR/TRE is a separate, authority-scoped
                # runtime binding. It remains opt-in and outside federation,
                # but the bounded type-filter contract is reproducible.
                TreSjurFirstDegreeFamilyProvider(self.config),
                Trt2BasisJurisprudenciaProvider(self.config),
                # Official TRT3 static appellate ementario.  It is exposed as
                # a curated opt-in source and is not treated as a general TRT3
                # search corpus.
                Trt3EmentarioJurisprudenciaProvider(self.config),
                # Official TRT9 NUGEP/NUGEPNAC curated appellate compilations.
                # This is a contextual opt-in source, not a general TRT9
                # corpus, so it remains outside the default federation.
                Trt9NugepnacJurisprudenciaProvider(self.config),
                # Official TRT4 curated súmulas/precedents page.  It is
                # contextual and opt-in, not the general Falcão corpus.
                Trt4SumulasJurisprudenciaProvider(self.config),
                # Official static appellate ementario. It is intentionally
                # opt-in: the collection is curated and does not expose a
                # national remote total like the PJe search.
                Trt2EmentarioJurisprudenciaProvider(self.config),
                # TRT15 exposes a public options catalog, while search currently
                # requires a CAPTCHA. Keep it visible for diagnostics but out of
                # the default federation until an authorized result contract is
                # available.
                Trt15JurisprudenciaProvider(self.config),
                # TRT8 publishes a public PJe JSON contract constrained to
                # second-degree appellate decisions.  It is part of the
                # default federation after live, fixture and detail gates
                # were closed locally.
                Trt8PjeJurisprudenciaProvider(self.config),
                TceSpJurisprudenciaProvider(self.config),
                TcePrViaJurisProvider(self.config),
                TjceInformativosProvider(self.config),
                TjacCjsgProvider(self.config),
                TjacBancoSentencasProvider(self.config),
                TjacEmentarioJurisprudenciaProvider(self.config),
                TjceCjsgProvider(self.config),
                TjceSjurisProvider(self.config),
                TjdfJurisProvider(self.config),
                TjgoProjudiJurisprudenciaProvider(self.config),
                TjalCjsgProvider(self.config),
                TjalTurmaRecursalEmentarioProvider(self.config),
                TjalEsmalBancoSentencasProvider(self.config),
                TjamCjsgProvider(self.config),
                TjmsCjsgProvider(self.config),
                TjmtJurisprudenciaApiProvider(self.config),
                TjesCjpgProvider(self.config),
                TjesJurisprudenciaProvider(self.config),
                TjesTurmaRecursalProvider(self.config),
                TjmsCjpgProvider(self.config),
                TjmaJurisconsultProvider(self.config),
                # Official curated TJMA bulletin editions.  Keep this source
                # opt-in at the capability level: it is not a complete CJSG
                # corpus and its PDFs are fetched only on demand.
                TjmaInformativosProvider(self.config),
                TjbaGraphqlProvider(self.config),
                TjpiJuspiProvider(self.config),
                TjprJurisprudenciaProvider(self.config),
                TjrnJurisprudenciaProvider(self.config),
                TjrrJurisProvider(self.config),
                TjroLiameProvider(self.config),
                # TJRO's general textual jurisprudence endpoint has a
                # reproducible bounded contract and participates in the
                # default federation.  Keep LIAME separate: it is a
                # qualified-precedent collection, not a substitute for this
                # court-wide search surface.
                TjroJurisprudenciaProvider(self.config),
                TjapBancoSentencasProvider(self.config),
                TjrjEprocJurisprudenciaProvider(self.config),
                TjrjEjurisProvider(self.config),
                TjrjBancoSentencasProvider(self.config),
                TjpaJurisprudenciaBffProvider(self.config),
                TjpbPjeJurisprudenciaProvider(self.config),
                # Keep REST as the provider's direct-construction default, but
                # let the federated client use the validated JSF fallback when
                # the REST transport is unavailable.
                TjpeJurisprudenciaProvider(self.config, transport="auto"),
                TjspCjsgProvider(self.config),
                TjspCjpgProvider(self.config),
                TjspEprocJurisprudenciaProvider(self.config),
                TjspNugepnacProvider(self.config),
                TreSpTemasProvider(self.config),
                TjrsSolrProvider(self.config),
                # TJMRS exposes a public exact-process appellate document
                # route.  Keep it opt-in: the portal does not expose a
                # reproducible free-text corpus contract.
                TjmrsJurisprudenciaProvider(self.config),
                TjscEprocJurisprudenciaProvider(self.config),
                TjtoJurisprudenciaProvider(self.config),
                TcuJurisprudenciaProvider(self.config),
                JusticaEleitoralSjurProvider(self.config),
                # The official TSE SJUR API is executable for a bounded,
                # single-window query and is exposed at runtime for explicit
                # use. It remains outside the default unified federation
                # because remote pagination is not proven.
                TseSjurJurisprudenciaProvider(self.config),
                TjseBoletimJurisprudenciaProvider(self.config),
                TjmgDspaceJurisprudenciaProvider(self.config),
                TjmgEjefBoletimJurisprudenciaProvider(self.config),
                # TJMG's modern public consultation API has a reproducible
                # CJSG contract; keep the legacy CAPTCHA form as fallback
                # inside the provider rather than routing around controls.
                TjmgJurisprudenciaProvider(self.config),
                # TJMMG exposes a bounded exact-process/date contract. Keep
                # it available in the normal runtime while its intentionally
                # opt-in capability prevents accidental federation of the
                # unbounded portal search.
                TjmmgJurisprudenciaApiProvider(self.config),
                Trf5JurisprudenciaProvider(self.config),
                # The exact-process route is executable but intentionally
                # opt-in: the portal's broader text search still lacks a
                # replayable HTTP contract and must not be federated by
                # accident.
                Trf3JurisprudenciaProvider(self.config),
                Trf2EprocJurisprudenciaProvider(self.config),
                Trf4EprocJurisprudenciaProvider(self.config),
                Trf6EprocJurisprudenciaProvider(self.config),
                # TRT6 legacy official portal exposes a bounded HTML search
                # contract with ementa, decision text and public document
                # links. The newer PJe SPA remains challenge-gated, but is
                # not required for this independent public surface.
                Trt6JurisprudenciaProvider(self.config),
            ]
            # Candidate providers remain outside this list. Technically
            # promoted providers, including TJRJ EJURIS, use the default path.
            if include_candidate_providers:
                # Diagnostic candidates are opt-in only.  TJSE deliberately
                # stops at the Turnstile boundary and is never routed by the
                # default federated client.  TJAP/TJMG follow the same rule:
                # their Juscraper-equivalent contracts are available for
                # diagnostics, but the public challenge remains explicit.
                provider_list.append(TjseJurisprudenciaProvider(self.config))
                provider_list.append(TjapTucujurisProvider(self.config))
                # TRT2 exposes a public options/filter catalog, while the
                # document route currently returns an explicit human
                # challenge. Keep the adapter diagnostic-only and opt-in.
                provider_list.append(Trt2PjeJurisprudenciaProvider(self.config))
                provider_list.append(FalcaoJtProvider(self.config))
                # TJMSP currently stops at the official portal's
                # access-control response and remains diagnostic-only.
                provider_list.append(TjmspJurisprudenciaProvider(self.config))
                # Candidate mode below only adds the 27 explicit per-UF
                # diagnostic TRE instances.
                # The official TRE SJUR route is one scoped adapter per UF.
                # Keep all 27 available for explicit diagnostics/selection,
                # but do not add them to the default federation until each
                # UF closes pagination, document and fixture gates.
                for tre_authority in TRE_AUTHORITIES:
                    provider_list.append(
                        TreSjurJurisprudenciaProvider(
                            self.config,
                            tribunal=tre_authority,
                        )
                    )
                    provider_list.append(
                        TreSjurFirstDegreeProvider(
                            self.config,
                            tribunal=tre_authority,
                        )
                    )
                # First-degree SJUR is already present in the normal runtime
                # as a separate family, so its records can never be mixed
                # with the second-degree family implicitly.
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
                judgment_date_from=str(
                    filters.get("judgment_date_from") or filters.get("judgment_from") or ""
                ),
                judgment_date_to=str(
                    filters.get("judgment_date_to") or filters.get("judgment_to") or ""
                ),
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
                case_class=str(filters.get("case_class") or filters.get("classe") or ""),
                judging_body=str(
                    filters.get("judging_body") or filters.get("orgao_julgador") or ""
                ),
                degree=str(filters.get("degree") or filters.get("grau") or ""),
                instance=str(filters.get("instance") or filters.get("instancia") or ""),
                branch=str(filters.get("branch") or filters.get("ramo") or ""),
                legal_area=str(filters.get("legal_area") or filters.get("area_juridica") or ""),
                authority=str(filters.get("authority") or filters.get("autoridade") or ""),
                collection=str(filters.get("collection") or filters.get("colecao") or ""),
                document_type=str(
                    filters.get("document_type") or filters.get("tipo_documento") or ""
                ),
                decision_type=str(
                    filters.get("decision_type") or filters.get("tipo_decisao") or ""
                ),
                election_year=str(filters.get("election_year") or filters.get("ano_eleicao") or ""),
                observations=str(filters.get("observations") or filters.get("observacoes") or ""),
                tags=str(filters.get("tags") or filters.get("etiquetas") or ""),
                municipality=str(filters.get("municipality") or filters.get("municipio") or ""),
                publication_source=str(
                    filters.get("publication_source") or filters.get("fonte_publicacao") or ""
                ),
                publication_number=str(
                    filters.get("publication_number") or filters.get("numero_publicacao") or ""
                ),
                publication_volume=str(
                    filters.get("publication_volume") or filters.get("volume_publicacao") or ""
                ),
                uf=str(filters.get("uf") or ""),
            )
        except ValueError as exc:
            raise InvalidQueryError(str(exc)) from exc
        provider = self._provider(source)
        capability = provider.get_capabilities()
        missing_scopes = sorted(
            name
            for name, status in capability.filter_semantics.items()
            if status == "required_scope"
            and not str(
                filters.get(name)
                or {
                    "authority": query.authority,
                    "branch": query.branch,
                    "degree": query.degree,
                    "instance": query.instance,
                    "collection": query.collection,
                }.get(name)
                or ""
            ).strip()
        )
        if missing_scopes:
            labels = ", ".join(missing_scopes)
            raise UnsupportedQueryError(
                f"A fonte {source!r} exige filtro de escopo explicito: {labels}."
            )
        # A single-source search has the same safety contract as federation:
        # exact identifiers must not be sent to a provider that does not
        # declare support.  Returning a warning after the call is too late,
        # because an endpoint can silently ignore the identifier and return
        # unrelated jurisprudence.
        identifier_filters = _identifier_filters(
            text=text,
            filters={
                "number": query.number,
                "party_name": query.party_name,
                "party_document": query.party_document,
                "lawyer_name": query.lawyer_name,
                "oab": query.oab,
                "precatory_number": query.precatory_number,
                "police_document": query.police_document,
                "cda": query.cda,
            },
        )
        unsupported_identifiers = identifier_filters.difference(capability.supported_filters)
        if unsupported_identifiers:
            labels = ", ".join(sorted(unsupported_identifiers))
            raise UnsupportedQueryError(
                f"A fonte {source!r} nao declara suporte ao filtro identificador: {labels}."
            )
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
                "judgment_date_from": query.judgment_date_from,
                "judgment_date_to": query.judgment_date_to,
                "updated_from": query.updated_from,
                "updated_to": query.updated_to,
                "source_origin": query.source_origin,
                "source_origins": query.source_origins,
                "fetch_details": query.fetch_details,
                "case_class": query.case_class,
                "judging_body": query.judging_body,
                "degree": query.degree,
                "instance": query.instance,
                "branch": query.branch,
                "legal_area": query.legal_area,
                "authority": query.authority,
                "collection": query.collection,
                "document_type": query.document_type,
                "decision_type": query.decision_type,
                "election_year": query.election_year,
                "observations": query.observations,
                "tags": query.tags,
                "municipality": query.municipality,
                "publication_source": query.publication_source,
                "publication_number": query.publication_number,
                "publication_volume": query.publication_volume,
                "uf": query.uf,
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
        _complete_filter_application(search_page, capability, query)
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
        ranking_version: str | None = None,
        mode: str | None = None,
        **filters: Any,
    ) -> dict[str, Any]:
        """Search multiple jurisprudence sources and return one aggregated payload."""

        if ranking_version not in {None, "legacy", RANKING_VERSION}:
            raise InvalidQueryError(f"versao de ranking desconhecida: {ranking_version}")
        effective_ranking_version = ranking_version
        if mode is not None and mode != "legacy":
            effective_ranking_version = ranking_version or RANKING_VERSION

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
                judgment_date_from=str(
                    filters.get("judgment_date_from") or filters.get("judgment_from") or ""
                ),
                judgment_date_to=str(
                    filters.get("judgment_date_to") or filters.get("judgment_to") or ""
                ),
            )
        except ValueError as exc:
            raise InvalidQueryError(str(exc)) from exc

        capabilities = {item.source: item for item in self.list_sources()}
        ignored_intent_filters = filters.pop("ignored_intent_filters", ())
        # Adaptive planning and provider contracts use canonical names.  The
        # single-source facade still accepts Portuguese aliases, but planning
        # with an alias would make a capable TRE look unsupported and could
        # exclude it from the selected wave.
        planning_filters = dict(filters)
        for filter_alias, canonical_filter in {
            "ano_eleicao": "election_year",
            "observacoes": "observations",
            "etiquetas": "tags",
            "municipio": "municipality",
            "fonte_publicacao": "publication_source",
            "numero_publicacao": "publication_number",
            "volume_publicacao": "publication_volume",
        }.items():
            if canonical_filter not in planning_filters and filter_alias in planning_filters:
                planning_filters[canonical_filter] = planning_filters[filter_alias]
            planning_filters.pop(filter_alias, None)
        search_plan: SearchPlan | None = None
        if mode is not None and mode != "legacy":
            search_plan = plan_live_search(
                text=text,
                filters={
                    name: value
                    for name, value in planning_filters.items()
                    if value not in (None, "", [], (), {})
                },
                capabilities=capabilities,
                mode=mode,
                sources=sources,
                ranking_version=effective_ranking_version or "legacy",
            )
            selected_sources = list(search_plan.sources)
        else:
            selected_sources = (
                list(sources) if sources is not None else self._default_unified_sources()
            )
        routing = route_unified_sources(
            selected_sources=selected_sources,
            capabilities=capabilities,
            text=text,
            opt_in_sources=frozenset(self.config.unified_opt_in_sources),
            # The explicit legacy mode is the compatibility escape hatch for
            # providers that predate the unified-search contract.  It is
            # intentionally limited to an explicit ``sources`` list so the
            # default federation never expands from the 53 unified sources to
            # every adapter in the catalog.  Adaptive/selected/all modes keep
            # the conservative contract and continue to skip non-unified
            # providers with an auditable reason.
            allow_non_unified=mode == "legacy" and sources is not None,
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
                "judgment_date_from": filters.get("judgment_date_from")
                or filters.get("judgment_from"),
                "judgment_date_to": filters.get("judgment_date_to") or filters.get("judgment_to"),
                "updated_from": filters.get("updated_from"),
                "updated_to": filters.get("updated_to"),
                "source_origin": filters.get("source_origin") or filters.get("origin"),
                "source_origins": filters.get("source_origins") or filters.get("origins"),
                "fetch_details": filters.get("fetch_details"),
                "case_class": filters.get("case_class") or filters.get("classe"),
                "judging_body": filters.get("judging_body") or filters.get("orgao_julgador"),
                "degree": filters.get("degree") or filters.get("grau"),
                "instance": filters.get("instance") or filters.get("instancia"),
                "branch": filters.get("branch") or filters.get("ramo"),
                "legal_area": filters.get("legal_area") or filters.get("area_juridica"),
                "authority": filters.get("authority") or filters.get("autoridade"),
                "collection": filters.get("collection") or filters.get("colecao"),
                "document_type": filters.get("document_type") or filters.get("tipo_documento"),
                "decision_type": filters.get("decision_type") or filters.get("tipo_decisao"),
                "election_year": filters.get("election_year") or filters.get("ano_eleicao"),
                "observations": filters.get("observations") or filters.get("observacoes"),
                "tags": filters.get("tags") or filters.get("etiquetas"),
                "municipality": filters.get("municipality") or filters.get("municipio"),
                "publication_source": filters.get("publication_source")
                or filters.get("fonte_publicacao"),
                "publication_number": filters.get("publication_number")
                or filters.get("numero_publicacao"),
                "publication_volume": filters.get("publication_volume")
                or filters.get("volume_publicacao"),
                "uf": filters.get("uf"),
            },
        )
        results: list[UnifiedSearchRecord] = []
        errors: list[dict[str, str]] = []
        # ``None`` is intentional when a provider does not prove its remote
        # total.  The legacy integer sentinel ``0`` is not allowed to leak
        # into this envelope as if it meant an explicit empty collection.
        source_totals: dict[str, int | None] = {}
        source_total_known: dict[str, bool | None] = {}
        source_access_status: dict[str, str | None] = {}
        source_extraction_status: dict[str, str | None] = {}
        # Preserve provider-level filter semantics without overloading the
        # legacy ``source_completeness`` shape consumed by existing clients.
        source_filters_applied: dict[str, dict[str, str]] = {}
        source_completeness: dict[str, dict[str, Any]] = {}
        source_outcomes_v2: dict[str, dict[str, Any]] = {}

        def fetch_source(
            source: str,
        ) -> tuple[
            list[UnifiedSearchRecord],
            int,
            SearchPage,
            int,
            int,
            list[dict[str, str]],
            float,
        ]:
            started_at = time.perf_counter()
            records: list[UnifiedSearchRecord] = []
            source_page = 1
            pages_fetched = 0
            page_result: SearchPage | None = None
            invalid_records = 0
            record_errors: list[dict[str, str]] = []
            seen_page_fingerprints: set[tuple[str, ...]] = set()
            page_limit_reached = False
            max_source_pages = max(1, int(getattr(self.config, "unified_max_pages", 25)))
            target = page * page_size
            if search_plan is not None:
                target = min(target, search_plan.per_source_budget)
            source_page_size = min(100, target)
            while len(records) < target:
                if pages_fetched >= max_source_pages:
                    page_limit_reached = True
                    break
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
                if page_result.access_status in {
                    "access_control_required",
                    "login_required",
                    "secret_or_restricted",
                }:
                    raise AccessControlRequiredError(
                        f"provider {source} reported restricted access status"
                    )
                if page_result.extraction_status in {
                    "failed",
                    "parser_contract_changed",
                    "unsupported_format",
                }:
                    raise ParserContractChangedError(
                        f"provider {source} reported an extraction contract change"
                    )
                if page_result.source_trace and page_result.source_trace.retrieval_status in {
                    "timeout",
                    "source_unavailable",
                    "tls_error",
                }:
                    raise SourceUnavailableError(
                        f"provider {source} reported an unavailable source"
                    )
                raw_results = list(page_result.results)
                # Some public endpoints ignore the requested page and return
                # the same window repeatedly.  Detect this before extending
                # the accumulator; otherwise federation can spend the whole
                # page budget on duplicates and falsely appear complete.
                page_fingerprint = (
                    page_result.source,
                    *(_record_identity(result) for result in raw_results),
                )
                if raw_results and page_fingerprint in seen_page_fingerprints:
                    page_result = replace(
                        page_result,
                        # Preserve an unknown completion state for legacy
                        # providers; the explicit reason still prevents the
                        # source from being reported as complete.
                        is_complete=(False if page_result.is_complete is False else None),
                        completeness_reason=(
                            "A fonte repetiu uma pagina sem novos identificadores."
                        ),
                    )
                    break
                seen_page_fingerprints.add(page_fingerprint)
                page_records: list[UnifiedSearchRecord] = []
                for record_index, result in enumerate(raw_results):
                    try:
                        if canonical:
                            canonical_records = search_page_to_canonical(
                                replace(page_result, results=[result])
                            )
                            if not canonical_records:
                                raise ValueError("canonicalization produced no record")
                            page_records.extend(canonical_records)
                        elif isinstance(result, JurisprudenceResult):
                            page_records.append(result)
                        else:
                            raise TypeError("provider returned an invalid record")
                    except Exception:
                        # Provider payloads can contain personal or legal data.
                        # Keep diagnostics useful without serializing the result
                        # or the exception, which may include the raw payload.
                        invalid_records += 1
                        record_errors.append(
                            _invalid_record_error(
                                source,
                                page=source_page,
                                record_index=record_index,
                            )
                        )
                native_ranks = _native_ranks_for_page(page_result)
                if native_ranks:
                    page_records = [
                        replace(record, native_rank=native_ranks.get(record.id))
                        if native_ranks.get(record.id) is not None
                        else record
                        for record in page_records
                    ]
                if not raw_results:
                    break
                records.extend(page_records)
                # Do not keep requesting pages forever when a provider returns
                # only malformed items and does not advertise completion. The
                # source is reported as partial below with its invalid count.
                if not page_records:
                    break
                if page_result.is_complete is True:
                    break
                # A legacy provider may return ``total=0`` both for a real
                # empty response and for an unknown remote count.  Only an
                # explicit total_known=True can authorize this stop; an
                # explicit page completion remains authoritative as well.
                if authoritative_total_reached(
                    reported_total=page_result.total,
                    total_known=page_result.total_known,
                    returned=len(raw_results),
                    accumulated=len(records),
                ):
                    break
                source_page += 1
            if page_result is None:
                raise InternalProviderError(f"provider {source} returned no search page")
            if page_limit_reached:
                page_result = replace(
                    page_result,
                    is_complete=(False if page_result.is_complete is False else None),
                    completeness_reason=(
                        f"A fonte atingiu o limite federado de {max_source_pages} paginas."
                    ),
                )
            return (
                records,
                page_result.total,
                page_result,
                pages_fetched,
                invalid_records,
                record_errors,
                (time.perf_counter() - started_at) * 1000,
            )

        def record_timeout(source: str) -> None:
            """Record a timeout without turning it into an empty source."""

            error = TimeoutError(f"tempo limite global da busca unificada excedido para {source}")
            if not continue_on_error:
                raise error
            error_payload = _source_error(source, error)
            errors.append(error_payload)
            source_completeness[source] = {
                "returned": 0,
                "reported_total": None,
                "pagination_mode": "timeout",
                "complete": False,
                "reason": "A fonte excedeu o tempo limite da consulta.",
                "pages_fetched": 0,
                "invalid_records": 0,
                "error_type": error_payload["error_type"],
                "error_message": error_payload["message"],
            }
            source_total_known[source] = None
            source_access_status[source] = None
            source_extraction_status[source] = None
            source_filters_applied[source] = {}
            source_outcomes_v2[source] = search_outcome_from_error(
                source, error_payload["error_type"], message=error_payload["message"]
            ).to_dict()

        def consume_future(source: str, future: Any, pending: set[Any]) -> None:
            if future in pending:
                record_timeout(source)
                return
            try:
                (
                    source_results,
                    total,
                    page_result,
                    pages_fetched,
                    invalid_records,
                    record_errors,
                    latency_ms,
                ) = future.result()
                source_totals[source] = total if page_result.total_known is True else None
                source_total_known[source] = page_result.total_known
                source_access_status[source] = _enum_value(page_result.access_status)
                source_extraction_status[source] = _enum_value(page_result.extraction_status)
                source_filters_applied[source] = dict(page_result.filters_applied)
                outcome_v2 = search_outcome_from_page(
                    page_result, latency_ms=latency_ms, pages=pages_fetched
                )
                if invalid_records:
                    outcome_v2 = replace(
                        outcome_v2,
                        status=SearchOutcomeStatus.PARTIAL,
                        message="A fonte retornou registros invalidos que foram omitidos.",
                    )
                source_outcomes_v2[source] = outcome_v2.to_dict()
                if record_errors:
                    errors.extend(record_errors)
                source_completeness[source] = {
                    "returned": len(source_results),
                    "reported_total": (total if page_result.total_known is True else None),
                    "pagination_mode": page_result.pagination_mode,
                    # A complete source page with dropped malformed records is
                    # still incomplete from the consumer's perspective.
                    "complete": False if invalid_records else page_result.is_complete,
                    "reason": (
                        "A fonte retornou registros invalidos que foram omitidos."
                        if invalid_records
                        else page_result.completeness_reason
                    ),
                    "pages_fetched": pages_fetched,
                    "invalid_records": invalid_records,
                }
                results.extend(source_results)
            except Exception as exc:
                if not continue_on_error:
                    raise
                if not isinstance(exc, NanoJurisError) and _classify_error(exc).error_type not in {
                    "NetworkConfigurationError",
                    "SslVerificationError",
                }:
                    exc = InternalProviderError(
                        f"provider {source} failed with an unexpected internal error"
                    )
                error_payload = _source_error(source, exc)
                errors.append(error_payload)
                source_completeness[source] = {
                    "returned": 0,
                    "reported_total": None,
                    "pagination_mode": "failed",
                    "complete": False,
                    "reason": "A fonte nao concluiu a consulta.",
                    "pages_fetched": 0,
                    # ``error_message`` is classified and sanitized by
                    # ``_source_error``; never copy the provider exception
                    # directly into this public envelope.
                    "error_type": error_payload["error_type"],
                    "error_message": error_payload["message"],
                }
                source_total_known[source] = None
                source_access_status[source] = None
                source_extraction_status[source] = None
                source_filters_applied[source] = {}
                source_outcomes_v2[source] = search_outcome_from_error(
                    source, error_payload["error_type"], message=error_payload["message"]
                ).to_dict()

        # Adaptive/selected/all plans are intentionally executed wave by wave.
        # The previous implementation created one executor for every source,
        # which made the plan metadata cosmetic and could issue twelve live
        # calls at once.  Legacy calls preserve their historical one-batch
        # behavior; the explicit live-search modes now honour the three-wave
        # contract and a global deadline.
        if search_plan is not None:
            wave_batches = [
                tuple(source for source in wave.sources if source in routing.searched)
                for wave in search_plan.waves
            ]
            wave_batches = [batch for batch in wave_batches if batch]
            total_deadline = time.monotonic() + min(
                self.config.unified_timeout,
                search_plan.wave_timeout_seconds * max(1, len(wave_batches)),
            )
            default_wave_timeout = search_plan.wave_timeout_seconds
        else:
            wave_batches = [tuple(routing.searched)] if routing.searched else []
            total_deadline = time.monotonic() + self.config.unified_timeout
            default_wave_timeout = self.config.unified_timeout

        for wave_sources in wave_batches:
            if not wave_sources:
                continue
            remaining = max(0.0, total_deadline - time.monotonic())
            if remaining <= 0:
                for source in wave_sources:
                    record_timeout(source)
                continue
            executor = ThreadPoolExecutor(
                max_workers=max(1, min(self.config.unified_max_workers, len(wave_sources)))
            )
            futures = {source: executor.submit(fetch_source, source) for source in wave_sources}
            done, pending = wait(futures.values(), timeout=min(default_wave_timeout, remaining))
            pending_set = set(pending)
            for source in wave_sources:
                consume_future(source, futures[source], pending_set)
            executor.shutdown(wait=False, cancel_futures=True)

        results = _rank_and_deduplicate(results, text=text)
        ranking_metadata: dict[str, dict[str, Any]] = {}
        query_intent: dict[str, Any] | None = None
        if effective_ranking_version == RANKING_VERSION:
            intent = LegalQueryAnalyzer().analyze(text, ignored_filters=ignored_intent_filters)
            ranker = LegalLiveRanker()
            ranked = ranker.diversify_near_ties(ranker.rank(intent, results))
            results = [item.record for item in ranked]
            for item in ranked:
                metadata = {
                    "relevance_score": item.relevance_score,
                    "matched_terms": list(item.matched_terms),
                    "matched_concepts": list(item.matched_concepts),
                    "match_reasons": list(item.match_reasons),
                    "bm25_score": item.bm25_score,
                    "bm25_version": BM25_VERSION,
                    "native_rank": item.native_rank,
                    "deduplication_group": item.deduplication_group,
                    "duplicate_sources": list(item.duplicate_sources),
                }
                # Keep the canonical identity as the public, reproducible
                # ranking key.  The browser projects records to a compact
                # ``source:id`` identity, so expose a non-authoritative alias
                # as well; without it the server ranked correctly but the UI
                # could not find the sidecar and rendered no evidence chips.
                canonical_key = _record_identity(item.record)
                ranking_metadata[canonical_key] = metadata
                source = str(getattr(item.record, "source", "") or "").strip()
                identifier = str(getattr(item.record, "id", "") or "").strip()
                if source and identifier:
                    ranking_metadata.setdefault(f"{source}:{identifier}", metadata)
            query_intent = intent.to_dict()
        if search_plan is not None and len(results) > search_plan.global_candidate_budget:
            results = results[: search_plan.global_candidate_budget]
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
        payload = {
            "sources": selected_sources,
            "searched_sources": routing.searched,
            "skipped_sources": [skip.to_dict() for skip in routing.skipped],
            "source_outcomes": build_source_outcomes(
                selected_sources=selected_sources,
                routed=routing,
                errors=errors,
            ),
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
            "source_total_known": source_total_known,
            "source_access_status": source_access_status,
            "source_extraction_status": source_extraction_status,
            "source_filters_applied": source_filters_applied,
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
        if search_plan is not None:
            payload.update(
                {
                    "mode": search_plan.mode.value,
                    "search_plan": search_plan.to_dict(),
                    "source_outcomes_v2": source_outcomes_v2,
                }
            )
        if effective_ranking_version == RANKING_VERSION:
            payload.update(
                {
                    "ranking_version": RANKING_VERSION,
                    # Keep the fielded lexical component discoverable even
                    # when the candidate batch is empty.  The per-result
                    # sidecar still carries the numeric score; this version
                    # marker lets API consumers reproduce the exact scorer
                    # without treating the live response as a document index.
                    "bm25_version": BM25_VERSION,
                    "ranking_complete": collection_complete,
                    "query_intent": query_intent,
                    "ranking": ranking_metadata,
                }
            )
        return payload

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
        ranking_version: str | None = None,
        mode: str | None = None,
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
            ranking_version=ranking_version,
            mode=mode,
            **filters,
        )
        query = {
            "text": text,
            "sources": payload["sources"],
            "searched_sources": payload["searched_sources"],
            "skipped_sources": payload["skipped_sources"],
            "source_outcomes": payload["source_outcomes"],
            "courts": courts or [],
            "types": types or [],
            "page": page,
            "page_size": page_size,
            "total_available": payload["total_available"],
            "total_returned": payload["total_returned"],
            "deduplicated_total": payload["deduplicated_total"],
            "source_totals": payload["source_totals"],
            "source_total_known": payload.get("source_total_known", {}),
            "source_access_status": payload.get("source_access_status", {}),
            "source_extraction_status": payload.get("source_extraction_status", {}),
            "source_filters_applied": payload.get("source_filters_applied", {}),
            "source_completeness": payload["source_completeness"],
            "sources_complete": payload["sources_complete"],
            "sources_partial": payload["sources_partial"],
            "sources_unknown": payload["sources_unknown"],
            "collection_complete": payload["collection_complete"],
            "completeness_reason": payload["completeness_reason"],
            "errors": payload["errors"],
            "ranking_version": payload.get("ranking_version", "legacy"),
            "bm25_version": payload.get("bm25_version"),
            "mode": payload.get("mode", "legacy"),
            "search_plan": payload.get("search_plan"),
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

    def sync_source_integral_pair(
        self,
        *,
        source: str,
        dataset_id: str,
        metadata_resource_id: str,
        text_resource_id: str,
        store: SQLiteStore,
        max_bytes: int = 50_000_000,
        label: str | None = None,
    ) -> dict[str, Any]:
        """Synchronize a metadata resource paired with an official text resource."""

        provider = self._provider(source)
        method = getattr(provider, "sync_integral_pair", None)
        if not callable(method):
            raise UnsupportedQueryError(f"Provider {source!r} does not sync integral pairs")
        result = method(
            dataset_id,
            metadata_resource_id,
            text_resource_id,
            store=store,
            max_bytes=max_bytes,
            label=label,
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
        opt_in_sources = frozenset(self.config.unified_opt_in_sources)
        return [
            capability.source
            for capability in self.list_sources()
            if (
                capability.category in JURISPRUDENCE_CATEGORIES
                and (
                    capability.supports_unified_search
                    or (capability.opt_in_unified_search and capability.source in opt_in_sources)
                )
            )
            or (
                capability.category == "specialized_context"
                and capability.opt_in_unified_search
                and capability.source in opt_in_sources
            )
        ]

    def _provider(self, source: str) -> JurisprudenceProvider:
        try:
            return self.providers[source]
        except KeyError as exc:
            available = ", ".join(sorted(self.providers))
            raise UnsupportedProviderError(
                f"Provider {source!r} is not registered. Available: {available}"
            ) from exc


def _complete_filter_application(
    page: SearchPage,
    capability: ProviderCapabilities,
    query: JurisprudenceQuery,
) -> None:
    """Fill missing active-filter dispositions at the client boundary.

    Providers may omit ``filters_applied`` while still declaring a contract.
    The client can safely report the disposition for filters that were actually
    requested; it never invents support for an undeclared filter. Provider
    supplied values remain authoritative.
    """

    values: dict[str, Any] = {
        "text": query.text,
        "all_words": query.all_words,
        "any_words": query.any_words,
        "without_words": query.without_words,
        "exact_phrase": query.exact_phrase,
        "number": query.number,
        "courts": query.courts,
        "types": query.types,
        "rapporteur": query.rapporteur,
        "published_from": query.published_from,
        "published_to": query.published_to,
        "updated_from": query.updated_from,
        "updated_to": query.updated_to,
        "judgment_date_from": query.judgment_date_from,
        "judgment_date_to": query.judgment_date_to,
        "source_origin": query.source_origin,
        "source_origins": query.source_origins,
        "fetch_details": query.fetch_details,
        "case_class": query.case_class,
        "judging_body": query.judging_body,
        "degree": query.degree,
        "instance": query.instance,
        "branch": query.branch,
        "legal_area": query.legal_area,
        "authority": query.authority,
        "collection": query.collection,
        "document_type": query.document_type,
        "decision_type": query.decision_type,
        "election_year": query.election_year,
        "observations": query.observations,
        "tags": query.tags,
        "municipality": query.municipality,
        "publication_source": query.publication_source,
        "publication_number": query.publication_number,
        "publication_volume": query.publication_volume,
        "uf": query.uf,
        "party_name": query.party_name,
        "party_document": query.party_document,
        "lawyer_name": query.lawyer_name,
        "oab": query.oab,
        "precatory_number": query.precatory_number,
        "police_document": query.police_document,
        "cda": query.cda,
    }
    for name, value in values.items():
        if _filter_value_present(value) and name not in page.filters_applied:
            page.filters_applied[name] = capability.filter_status(name)


def _filter_value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list | tuple | set):
        return bool(value)
    return bool(value)


def _native_ranks_for_page(page: SearchPage) -> dict[str, int]:
    """Extract a provider's native ordering without manufacturing relevance.

    Providers that expose an explicit rank/score are authoritative.  For a
    provider that declares relevance ordering but only returns an ordered
    window, the position in that window is the native rank.  Date/editorial
    ordering is deliberately excluded so the lexical reranker cannot mistake
    recency for source relevance.
    """

    rows = list(page.results)
    if not rows:
        return {}
    explicit: dict[str, int] = {}
    scores: list[tuple[str, float]] = []
    for result in rows:
        identifier_value = getattr(result, "id", None)
        if identifier_value is None:
            continue
        raw = getattr(result, "raw", None) or {}
        identifier = str(identifier_value)
        for key in ("native_rank", "rank", "position", "order", "ordem"):
            value = raw.get(key)
            if value is None:
                continue
            try:
                rank = int(value)
            except (TypeError, ValueError):
                continue
            if rank > 0:
                explicit[identifier] = rank
                break
        for key in ("score", "_score", "search_score", "relevance_score"):
            value = raw.get(key)
            if value is None:
                continue
            try:
                score = float(value)
            except (TypeError, ValueError):
                continue
            if score == score:
                scores.append((identifier, score))
                break
    if explicit:
        return explicit
    if scores:
        ordered = sorted(scores, key=lambda item: (-item[1], item[0]))
        return {identifier: index + 1 for index, (identifier, _) in enumerate(ordered)}
    ordering = str(page.ordering or "").casefold()
    if "relev" not in ordering and "score" not in ordering and "rank" not in ordering:
        return {}
    base = max(0, (page.page - 1) * page.page_size)
    return {str(result.id): base + index + 1 for index, result in enumerate(rows)}


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
    record_type = (
        getattr(record, "decision_type", None)
        or getattr(record, "precedent_type", None)
        or type(record).__name__
    )
    semantic_fields = {
        name: getattr(record, name, None)
        for name in (
            "subject",
            "question",
            "thesis",
            "summary",
            "rapporteur",
            "judgment_date",
            "publication_date",
            "updated_at",
            "status",
            "document_type",
        )
    }
    cross_source = _cross_source_identity(record, case_number=case_number, record_type=record_type)
    if cross_source is not None:
        return cross_source
    return identity_key(
        source=getattr(record, "source", ""),
        court=getattr(record, "court", ""),
        identifier=getattr(record, "id", ""),
        number=case_number,
        record_type=record_type,
        semantic_fields=semantic_fields,
    )


def _cross_source_identity(
    record: UnifiedSearchRecord,
    *,
    case_number: object,
    record_type: object,
) -> str | None:
    """Deduplicate the same CNJ decision published by multiple portals."""

    digits = re.sub(r"\D", "", str(case_number or ""))
    court = str(getattr(record, "court", "") or "").strip().casefold()
    kind = str(record_type or "").strip().casefold()
    event_date_raw = str(
        getattr(record, "judgment_date", None)
        or getattr(record, "publication_date", None)
        or getattr(record, "updated_at", None)
        or ""
    ).strip()
    event_date = normalize_date_value(event_date_raw) or event_date_raw
    if len(digits) != 20 or not court or not kind or not event_date:
        return None
    return "cross:decision:" + "|".join((court, digits, kind, event_date))


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


def _invalid_record_error(
    source: str,
    *,
    page: int,
    record_index: int,
) -> dict[str, str]:
    """Describe a dropped provider item without retaining its payload.

    A malformed provider result can contain a complete legal document or
    personal data.  The error envelope therefore records only stable location
    metadata; callers can diagnose the adapter without leaking the raw result
    or an exception string containing the response body.
    """

    return {
        "source": source,
        "scope": "record",
        "error_type": "InvalidRecordError",
        "message": "A fonte retornou um registro invalido; o item foi omitido.",
        "page": str(page),
        "record_index": str(record_index),
    }


def _enum_value(value: object) -> str | None:
    """Serialize optional enum metadata without imposing a new dependency."""

    if value is None:
        return None
    raw = getattr(value, "value", value)
    return str(raw)


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
    # ``requests.exceptions.SSLError`` often exposes only the message through
    # ``str(exc)`` (for example ``certificate verify failed``), omitting the
    # exception class. Inspect the exception chain types as well so a TLS
    # failure cannot be downgraded to a generic internal error—or an empty
    # provider result—by the federated collector.
    ssl_exception = any("ssl" in type(item).__name__.lower() for item in _exception_chain(exc))
    if ("ssl" in lowered or ssl_exception) and (
        "certificate" in lowered or "certificado" in lowered or ssl_exception
    ):
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
        message=safe_error_message(exc),
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
