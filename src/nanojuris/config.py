"""Runtime configuration for NanoJuris."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import wraps
from typing import Any


@dataclass(slots=True)
class NanoJurisConfig:
    """Configuration shared by clients and providers."""

    timeout: float = 20.0
    verify_ssl: bool = True
    trust_env: bool = field(default_factory=lambda: _env_bool("NANOJURIS_TRUST_ENV", True))
    user_agent: str = "NanoJuris/0.3.0 (+https://github.com/ndtj/nanojuris)"
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
    tce_sp_url: str = "https://www.tce.sp.gov.br"
    tre_sp_url: str = "https://www.tre-sp.jus.br"
    tjsp_url: str = "https://www.tjsp.jus.br"
    tjdf_juris_url: str = "https://pesquisajuris.tjdft.jus.br"
    tnu_eproc_jurisprudencia_url: str = "https://eproctnu.cjf.jus.br/eproc"
    trf2_eproc_jurisprudencia_url: str = "https://eproc.trf2.jus.br/eproc"
    trf4_eproc_jurisprudencia_url: str = "https://jurisprudencia.trf4.jus.br/eproc2trf4"
    trf6_eproc_jurisprudencia_url: str = "https://eproc-jur.trf6.jus.br/eproc"
    tjac_cjsg_url: str = "https://esaj.tjac.jus.br/cjsg"
    tjce_cjsg_url: str = "https://esaj.tjce.jus.br/cjsg"
    tjce_sjuris_url: str = "https://gateway.tjce.jus.br/sjuris/api/v1"
    tjmt_jurisprudencia_url: str = "https://jurisprudencia.tjmt.jus.br"
    tjto_jurisprudencia_url: str = "https://jurisprudencia.tjto.jus.br"
    tjma_jurisconsult_url: str = "https://apijuris.tjma.jus.br/v1"
    tjro_liame_url: str = "https://liame.tjro.jus.br"
    tjal_cjsg_url: str = "https://www2.tjal.jus.br/cjsg"
    tjam_cjsg_url: str = "https://consultasaj.tjam.jus.br/cjsg"
    tjms_cjsg_url: str = "https://esaj.tjms.jus.br/cjsg"
    tjsp_cjsg_url: str = "https://esaj.tjsp.jus.br/cjsg"
    tjsp_eproc_url: str = "https://eproc-consulta.tjsp.jus.br/consulta_1g"
    tjrj_eproc_jurisprudencia_url: str = "https://eproc1g.tjrj.jus.br/eproc"
    tjsc_eproc_jurisprudencia_url: str = "https://eprocwebcon.tjsc.jus.br/consulta1g"
    tjgo_projudi_url: str = "https://projudi.tjgo.jus.br"
    tjpi_juspi_url: str = "https://jurisprudencia.tjpi.jus.br"
    tjpr_jurisprudencia_url: str = "https://portal.tjpr.jus.br"
    tjpa_jurisprudencia_url: str = "https://jurisprudencia.tjpa.jus.br"
    tjpb_pje_jurisprudencia_url: str = "https://pje-jurisprudencia.tjpb.jus.br"
    tjpe_jurisprudencia_url: str = "https://consultajurisprudencia.app.tjpe.jus.br"
    tjba_graphql_url: str = "https://jurisprudenciaws.tjba.jus.br"
    tjrr_juris_url: str = "https://jurisprudencia.tjrr.jus.br"
    tjrs_jurisprudencia_url: str = "https://www.tjrs.jus.br"
    trf5_jurisprudencia_url: str = "https://jurisprudencia.trf5.jus.br"
    cjf_trf1_jurisprudencia_url: str = "https://jurisprudencia.cjf.jus.br"
    tcu_jurisprudencia_url: str = "https://sites.tcu.gov.br"
    tse_sjur_url: str = "https://jurisprudencia.tse.jus.br"
    tse_sjur_api_url: str = "https://sjur-pesquisa-api.tse.jus.br"
    # Conservative default for public court endpoints; tests and controlled
    # local fixtures can explicitly set this to zero.
    rate_limit_interval: float = 0.25
    unified_max_workers: int = 6
    unified_timeout: float = 60.0


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
