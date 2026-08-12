"""Runtime configuration for NanoJuris."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class NanoJurisConfig:
    """Configuration shared by clients and providers."""

    timeout: float = 20.0
    verify_ssl: bool = True
    trust_env: bool = field(default_factory=lambda: _env_bool("NANOJURIS_TRUST_ENV", True))
    user_agent: str = "NanoJuris/0.2.0 (+https://github.com/ndtj/nanojuris)"
    bnp_api_url: str = "https://pangeabnp.pdpj.jus.br/api/v1"
    comunica_pje_url: str = "https://comunicaapi.pje.jus.br"
    stf_juris_url: str = "https://jurisprudencia.stf.jus.br"
    stf_informativo_data_url: str = (
        "https://www.stf.jus.br/arquivo/cms/informativoSTF/anexo/"
        "Informativo_Dados/Dados_InformativosSTF.xlsx"
    )
    stf_informativo_url: str = "https://portal.stf.jus.br/textos/verTexto.asp"
    stf_portal_url: str = "https://portal.stf.jus.br"
    stj_url: str = "https://processo.stj.jus.br"
    stj_scon_url: str = "https://scon.stj.jus.br"
    stm_jurisprudencia_url: str = "https://jurisprudencia.stm.jus.br"
    tst_jurisprudencia_url: str = "https://jurisprudencia.tst.jus.br"
    tst_jurisprudencia_api_url: str = "https://jurisprudencia-backend2.tst.jus.br"
    tce_sp_url: str = "https://www.tce.sp.gov.br"
    tre_sp_url: str = "https://www.tre-sp.jus.br"
    tjsp_url: str = "https://www.tjsp.jus.br"
    tjdf_juris_url: str = "https://pesquisajuris.tjdft.jus.br"
    tnu_eproc_jurisprudencia_url: str = "https://eproctnu.cjf.jus.br/eproc"
    trf2_eproc_jurisprudencia_url: str = "https://eproc.trf2.jus.br/eproc"
    trf4_eproc_jurisprudencia_url: str = "https://jurisprudencia.trf4.jus.br/eproc2trf4"
    trf6_eproc_jurisprudencia_url: str = "https://eproc-jur.trf6.jus.br/eproc"
    tjac_cjsg_url: str = "https://esaj.tjac.jus.br/cjsg"
    tjac_esaj_url: str = "https://esaj.tjac.jus.br"
    tjal_cjsg_url: str = "https://www2.tjal.jus.br/cjsg"
    tjam_cjsg_url: str = "https://consultasaj.tjam.jus.br/cjsg"
    tjms_cjsg_url: str = "https://esaj.tjms.jus.br/cjsg"
    tjsp_esaj_url: str = "https://esaj.tjsp.jus.br"
    tjsp_cjsg_url: str = "https://esaj.tjsp.jus.br/cjsg"
    tjsp_eproc_url: str = "https://eproc-consulta.tjsp.jus.br/consulta_1g"
    tjrj_eproc_jurisprudencia_url: str = "https://eproc1g.tjrj.jus.br/eproc"
    tjsc_eproc_jurisprudencia_url: str = "https://eprocwebcon.tjsc.jus.br/consulta1g"
    tjgo_projudi_url: str = "https://projudi.tjgo.jus.br"
    tjpi_juspi_url: str = "https://jurisprudencia.tjpi.jus.br"
    tjpa_jurisprudencia_url: str = "https://jurisprudencia.tjpa.jus.br"
    tjpb_pje_jurisprudencia_url: str = "https://pje-jurisprudencia.tjpb.jus.br"
    tjrs_jurisprudencia_url: str = "https://www.tjrs.jus.br"
    trf5_jurisprudencia_url: str = "https://jurisprudencia.trf5.jus.br"
    cjf_trf1_jurisprudencia_url: str = "https://jurisprudencia.cjf.jus.br"
    tcu_jurisprudencia_url: str = "https://sites.tcu.gov.br"
    # Conservative default for public court endpoints; tests and controlled
    # local fixtures can explicitly set this to zero.
    rate_limit_interval: float = 0.25
    unified_max_workers: int = 6
    unified_timeout: float = 60.0


def configure_requests_session(session: Any, config: NanoJurisConfig) -> Any:
    """Apply shared HTTP configuration to a requests-compatible session."""

    if hasattr(session, "trust_env"):
        session.trust_env = config.trust_env
    if hasattr(session, "verify"):
        session.verify = config.verify_ssl
    return session


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}
