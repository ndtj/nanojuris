"""Runtime configuration for NanoJuris."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

from nanojuris.governance import DEFAULT_OPERATIONAL_POLICY


@dataclass(slots=True)
class NanoJurisConfig:
    """Configuration shared by clients and providers."""

    timeout: float = 20.0
    verify_ssl: bool = True
    trust_env: bool = field(default_factory=lambda: _env_bool("NANOJURIS_TRUST_ENV", True))
    user_agent: str = "NanoJuris/0.4.0 (+https://github.com/ndtj/nanojuris)"
    bnp_api_url: str = "https://pangeabnp.pdpj.jus.br/api/v1"
    cnj_jurisprudencia_url: str = "https://atos.cnj.jus.br"
    tjce_informativos_url: str = "https://www.tjce.jus.br"
    stf_juris_url: str = "https://jurisprudencia.stf.jus.br"
    stf_informativo_data_url: str = (
        "https://www.stf.jus.br/arquivo/cms/informativoSTF/anexo/"
        "Informativo_Dados/Dados_InformativosSTF.xlsx"
    )
    stf_informativo_url: str = "https://portal.stf.jus.br/textos/verTexto.asp"
    stf_portal_url: str = "https://portal.stf.jus.br"
    stj_url: str = "https://processo.stj.jus.br"
    stj_scon_url: str = "https://scon.stj.jus.br"
    stj_dados_abertos_url: str = "https://dadosabertos.web.stj.jus.br"
    stm_jurisprudencia_url: str = "https://jurisprudencia.stm.jus.br"
    tst_jurisprudencia_url: str = "https://jurisprudencia.tst.jus.br"
    tst_jurisprudencia_api_url: str = "https://jurisprudencia-backend2.tst.jus.br"
    # Official TRT15 jurisprudence SPA.  Search is challenge-protected; the
    # provider remains diagnostic-only until a public result contract exists.
    trt15_jurisprudencia_url: str = "https://jurisprudencia.trt15.jus.br"
    # Public official TRT2 BASIS DSpace collection with curated appellate
    # jurisprudence bulletins.  This is deliberately separate from the PJe
    # search surface, whose document route may require an interactive
    # challenge.
    trt2_basis_jurisprudencia_url: str = "https://basis.trt2.jus.br"
    # Public TRT2 PJe jurisprudence SPA/backend.  The options and filter
    # catalog are public; document search currently stops at a human challenge
    # and is therefore diagnostic-only until an official result contract exists.
    trt2_pje_jurisprudencia_url: str = "https://pje.trt2.jus.br"
    # Official national Falcao JT repository. The result contract is
    # intermittent/blocked and therefore diagnostic-only.
    falcao_jt_url: str = "https://jurisprudencia.jt.jus.br/"
    falcao_jt_api_url: str = "https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api"
    # Public static TRT2 appellate ementario topic pages.  Separate from the
    # challenge-protected PJe search and intentionally opt-in in federation.
    trt2_ementario_url: str = "https://trt2.jus.br"
    # Public TRT8 PJe jurisprudence SPA/backend.  The adapter fixes the
    # appellate scope (2nd instance + Acórdão) and remains opt-in until its
    # promotion ledger and federated smoke are closed.
    trt8_pje_jurisprudencia_url: str = "https://pje.trt8.jus.br"
    # Official TRT3 curated appellate ementario volume.  This is a bounded
    # static collection, not a general search endpoint, and remains opt-in.
    trt3_ementario_jurisprudencia_url: str = (
        "https://as1.trt3.jus.br/bd-trt3/bitstream/handle/11103/23582/"
        "Ement%C3%A1rio%20de%20Jurisprud%C3%AAncia%20n.%2012%20-%20dezembro%202016.pdf"
        "?sequence=1&isAllowed=y"
    )
    # Official TRT9 NUGEP/NUGEPNAC curated appellate compilation. This is an
    # opt-in contextual PDF surface, not the general TRT9 jurisprudence corpus.
    trt9_nugepnac_jurisprudencia_url: str = (
        "https://www.trt9.jus.br/bancojurisprudencia/api/v1/"
        "jurisprudencia/pdf-simplificado?tribunal=TRT9"
    )
    # Official TRT4 curated súmulas/precedents page.  This is an opt-in
    # contextual collection, not the general Falcão search corpus.
    trt4_sumulas_jurisprudencia_url: str = "https://www.trt4.jus.br/portais/trt4/sumulas"
    # Official TRT6 appellate jurisprudence SPA and legacy acórdãos portal.
    # Both public search surfaces currently require an interactive reCAPTCHA;
    # the provider is diagnostic-only until an authorized non-challenge
    # result contract is published.
    trt6_jurisprudencia_url: str = "https://pje.trt6.jus.br"
    trt6_acordaos_url: str = "https://apps.trt6.jus.br"
    tce_sp_url: str = "https://www.tce.sp.gov.br"
    tce_pr_viajuris_url: str = "https://viajuris.tce.pr.gov.br"
    tre_sp_url: str = "https://www.tre-sp.jus.br"
    tjsp_url: str = "https://www.tjsp.jus.br"
    tjdf_juris_url: str = "https://pesquisajuris.tjdft.jus.br"
    # The structured API belongs to the same TJDFT provider. It remains
    # explicitly selectable so deployments can retain the legacy HTML route.
    tjdf_juris_api_url: str = "https://jurisdf.tjdft.jus.br"
    # The documented JSON surface returns bounded ementa plus inteiro teor
    # when ``fetch_details`` is requested. Keep it as the default runtime
    # path; the legacy SISTJ HTML flow remains available explicitly for
    # compatibility and replay fixtures.
    tjdf_juris_api_enabled: bool = True
    # Public TNU jurisprudence module announced by CJF.  Keep it separate
    # from the legacy eproc host, which redirects the public entry point to
    # SSO before the jurisprudence form can be reached.
    tnu_eproc_jurisprudencia_url: str = "https://eproctnu-jur.cjf.jus.br/eproc"
    trf2_eproc_jurisprudencia_url: str = "https://eproc.trf2.jus.br/eproc"
    trf4_eproc_jurisprudencia_url: str = "https://jurisprudencia.trf4.jus.br/eproc2trf4"
    trf6_eproc_jurisprudencia_url: str = "https://eproc-jur.trf6.jus.br/eproc"
    tjac_cjsg_url: str = "https://esaj.tjac.jus.br/cjsg"
    # Public official TJAC appellate Ementario volume. It is a bounded static
    # collection and does not claim a complete remote total.
    tjac_ementario_url: str = (
        "https://www.tjac.jus.br/wp-content/uploads/2026/07/Ementario_TJAC_Vol_XXX_2026.pdf"
    )
    # Official curated first-instance sentence bank published by the TJAC
    # Corregedoria; separate from general e-SAJ jurisprudence.
    tjac_banco_sentencas_url: str = "https://www.tjac.jus.br/coger/banco-de-sentencas/"
    tjce_cjsg_url: str = "https://esaj.tjce.jus.br/cjsg"
    tjce_sjuris_url: str = "https://gateway.tjce.jus.br/sjuris/api/v1"
    tjmt_jurisprudencia_url: str = "https://jurisprudencia.tjmt.jus.br"
    # Public TJES jurisprudence API.  The CJPG first-instance collection is
    # selected explicitly by the provider with core=pje1g.
    tjes_jurisprudencia_url: str = "https://sistemas.tjes.jus.br/consulta-jurisprudencia"
    # Public first-instance TJAP Banco de Sentenças Livewire surface.
    tjap_banco_sentencas_url: str = "https://bancosentencas.tjap.jus.br"
    tjto_jurisprudencia_url: str = "https://jurisprudencia.tjto.jus.br"
    tjma_jurisconsult_url: str = "https://apijuris.tjma.jus.br/v1"
    # Official curated monthly TJMA jurisprudence bulletins.  This is an
    # opt-in collection of PDF editions, distinct from the CAPTCHA-gated
    # JurisConsult general search.
    tjma_informativos_url: str = "https://www.tjma.jus.br/midia/pje/pagina/hotsite/509874"
    # Public DSpace collections with individual TJMG jurisprudence records;
    # separate from the legacy CAPTCHA-protected search form.
    tjmg_dspace_jurisprudencia_url: str = "https://bd.tjmg.jus.br"
    # Public TJMG jurisprudence SPA/API.  The API is the official backend of
    # consulta-jurisprudencia.tjmg.jus.br and does not require a user token for
    # bounded search or document retrieval.
    tjmg_jurisprudencia_api_url: str = "https://jurisprudencia-api.tjmg.jus.br"
    tjmg_jurisprudencia_portal_url: str = "https://consulta-jurisprudencia.tjmg.jus.br"
    # Public TJRO JURIS Elasticsearch surface. Detail and filter limitations
    # remain explicit in the provider contract.
    tjro_jurisprudencia_url: str = "https://juris-back.tjro.jus.br"
    tjro_liame_url: str = "https://liame.tjro.jus.br"
    tjal_cjsg_url: str = "https://www2.tjal.jus.br/cjsg"
    tjal_turma_recursal_index_url: str = "https://aceco.tjal.jus.br/?pag=juizados_jurisprudencias"
    tjal_turma_recursal_volume_url: str = (
        "https://aceco.tjal.jus.br/juizados/relatorios/Ementas-3.pdf"
    )
    # Official ESMAL selected first-instance sentence bank. It is federated as
    # a clearly labelled partial CJPG collection; total_unknown and curated
    # scope remain visible in every SearchPage.
    tjal_esmal_banco_sentencas_url: str = "https://esmal.tjal.jus.br/indexS.php?pag=ler"
    tjam_cjsg_url: str = "https://consultasaj.tjam.jus.br/cjsg"
    tjms_cjsg_url: str = "https://esaj.tjms.jus.br/cjsg"
    tjsp_cjsg_url: str = "https://esaj.tjsp.jus.br/cjsg"
    # Public first-instance jurisprudence (CJPG) surface on e-SAJ.
    tjsp_cjpg_url: str = "https://esaj.tjsp.jus.br"
    # TJMS exposes the same public e-SAJ CJPG form on its own host.  Keep the
    # host configurable so deployments can use an approved mirror without
    # changing provider code.
    tjms_cjpg_url: str = "https://esaj.tjms.jus.br"
    tjsp_eproc_url: str = "https://eproc-consulta.tjsp.jus.br/consulta_1g"
    tjrj_eproc_jurisprudencia_url: str = "https://eproc1g.tjrj.jus.br/eproc"
    # Public TJRJ EJURIS/CJSG ASP.NET surface (kept separate from eproc).
    tjrj_ejuris_url: str = "https://www3.tjrj.jus.br"
    # Official curated first-instance selected-sentence index.  This is a
    # separate collection from the appellate eJURIS/eproc surfaces and is
    # intentionally opt-in because the PDF is an index, not a complete CJPG
    # corpus.
    tjrj_banco_sentencas_url: str = (
        "https://portaltj.tjrj.jus.br/documents/10136/18187/banco-sentencas.pdf"
    )
    tjsc_eproc_jurisprudencia_url: str = "https://eprocwebcon.tjsc.jus.br/consulta1g"
    tjgo_projudi_url: str = "https://projudi.tjgo.jus.br"
    tjpi_juspi_url: str = "https://jurisprudencia.tjpi.jus.br"
    tjpr_jurisprudencia_url: str = "https://portal.tjpr.jus.br"
    # Public TJRN portal. The adapter is enabled after bounded live and
    # reproducible-contract gates; degree-specific bindings remain separate.
    tjrn_jurisprudencia_url: str = "https://jurisprudencia.tjrn.jus.br"
    tjpa_jurisprudencia_url: str = "https://jurisprudencia.tjpa.jus.br"
    tjpb_pje_jurisprudencia_url: str = "https://pje-jurisprudencia.tjpb.jus.br"
    tjpe_jurisprudencia_url: str = "https://consultajurisprudencia.app.tjpe.jus.br"
    # Legacy public JSF/RichFaces surface used by Juscraper as a transport
    # fallback when the structured REST surface is unavailable.
    tjpe_juscraper_url: str = "https://www.tjpe.jus.br/consultajurisprudenciaweb/xhtml/consulta"
    tjba_graphql_url: str = "https://jurisprudenciaws.tjba.jus.br"
    tjrr_juris_url: str = "https://jurisprudencia.tjrr.jus.br"
    # Public TJSE judicial jurisprudence form.  The result submission is
    # protected by Cloudflare Turnstile and therefore remains diagnostic-only
    # until a legitimate public result contract is available.
    tjse_jurisprudencia_url: str = (
        "https://www.tjse.jus.br/Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse"
    )
    # Public monthly Boletim Jurídico ementas; independent from the protected
    # judicial search form above.
    tjse_boletim_jurisprudencia_url: str = "https://diario.tjse.jus.br"
    tjrs_jurisprudencia_url: str = "https://www.tjrs.jus.br"
    # Public TJMRS jurisprudence route.  The adapter is intentionally exact
    # process and opt-in because no reproducible free-text corpus contract was
    # observed.
    tjmrs_jurisprudencia_url: str = "https://www.tjmrs.jus.br"
    # Public TJMMG and TJMSP jurisprudence applications.  Both are diagnostic
    # opt-in bindings until the public response/pagination contracts are
    # bounded and reproducible.
    tjmmg_jurisprudencia_url: str = "https://jurisprudencia.tjmmg.jus.br"
    tjmsp_jurisprudencia_url: str = "https://jurisprudencia-client.tjmsp.jus.br"
    # Official TJMSP frontend-discovered API.  It remains diagnostic until a
    # bounded public result contract is available; the URL is exposed so a
    # future, explicitly authorized probe can use the shared transport.
    tjmsp_jurisprudencia_api_url: str = "https://api-jurisprudencia.tjmsp.jus.br/v1"
    # Public TRF3 appellate document lookup.  The exact-process route is
    # implemented independently from the portal's unreplayed free-text form.
    trf3_jurisprudencia_url: str = "https://web.trf3.jus.br"
    trf5_jurisprudencia_url: str = "https://jurisprudencia.trf5.jus.br"
    cjf_trf1_jurisprudencia_url: str = "https://jurisprudencia.cjf.jus.br"
    tcu_jurisprudencia_url: str = "https://sites.tcu.gov.br"
    tse_sjur_url: str = "https://jurisprudencia.tse.jus.br"
    tse_sjur_api_url: str = "https://sjur-pesquisa-api.tse.jus.br"
    # Public TSE SJUR document service discovered in the official frontend.
    tse_sjur_document_url: str = "https://sjur-servicos.tse.jus.br/sjur-servicos/rest"
    # Conservative default for public court endpoints; tests and controlled
    # local fixtures can explicitly set this to zero.  The two-second floor is
    # the NanoJuris bounded-probe policy, not a claim about a source's terms.
    rate_limit_interval: float = DEFAULT_OPERATIONAL_POLICY.min_provider_request_interval_seconds
    live_cache_ttl_seconds: float = DEFAULT_OPERATIONAL_POLICY.live_cache_ttl_seconds
    telemetry_retention_days: int = DEFAULT_OPERATIONAL_POLICY.telemetry_retention_days
    bounded_probe_max_pages: int = DEFAULT_OPERATIONAL_POLICY.max_bounded_pages
    unified_max_workers: int = 6
    unified_timeout: float = 60.0
    # Hard ceiling for one source in a federated request. A provider that does
    # not expose a trustworthy total must never make federation unbounded.
    unified_max_pages: int = 25
    # Explicit rollout list for technically validated but not-yet-default
    # providers. Empty by default: legal/release approval is never inferred.
    unified_opt_in_sources: tuple[str, ...] = ()


def configure_requests_session(session: Any, config: NanoJurisConfig) -> Any:
    """Apply shared HTTP policy to a requests-compatible session.

    Providers may call ``get``, ``post`` or ``request`` directly. Wrapping the
    session request boundary keeps SSL verification, timeout and User-Agent
    behavior consistent without duplicating policy in every provider.
    """

    if hasattr(session, "trust_env"):
        session.trust_env = config.trust_env
    if hasattr(session, "verify"):
        session.verify = config.verify_ssl
    if callable(getattr(session, "request", None)) and not getattr(
        session, "_nanojuris_http_configured", False
    ):
        original_request = session.request

        @wraps(original_request)
        def configured_request(*args: Any, **kwargs: Any) -> Any:
            headers = dict(kwargs.get("headers") or {})
            if not any(str(name).lower() == "user-agent" for name in headers):
                headers["User-Agent"] = config.user_agent
            kwargs["headers"] = headers
            if kwargs.get("timeout") is None:
                kwargs["timeout"] = config.timeout
            if kwargs.get("verify") is None:
                kwargs["verify"] = config.verify_ssl
            return original_request(*args, **kwargs)

        session.request = configured_request
        session._nanojuris_http_configured = True
    return session


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}
