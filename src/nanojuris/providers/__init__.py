"""Provider implementations."""

from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.providers.bnp_pangea import BnpPangeaProvider
from nanojuris.providers.cjf_jurisprudencia import CjfJurisprudenciaProvider
from nanojuris.providers.comunica_pje import ComunicaPjeProvider
from nanojuris.providers.eproc_jurisprudencia_federal import (
    FederalEprocJurisprudenciaProvider,
    TnuEprocJurisprudenciaProvider,
    Trf2EprocJurisprudenciaProvider,
    Trf6EprocJurisprudenciaProvider,
)
from nanojuris.providers.stf_juris import StfJurisProvider
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

__all__ = [
    "BnpPangeaProvider",
    "CjfJurisprudenciaProvider",
    "ComunicaPjeProvider",
    "FederalEprocJurisprudenciaProvider",
    "JurisprudenceProvider",
    "StfJurisProvider",
    "StjSconProvider",
    "StmJurisprudenciaProvider",
    "TceSpJurisprudenciaProvider",
    "TjacCjsgProvider",
    "TjacEsajCpopgProvider",
    "TjdfJurisProvider",
    "TjgoProjudiJurisprudenciaProvider",
    "TjpaJurisprudenciaBffProvider",
    "TjpbPjeJurisprudenciaProvider",
    "TjrjEprocJurisprudenciaProvider",
    "TjalCjsgProvider",
    "TjamCjsgProvider",
    "TjmsCjsgProvider",
    "TjspCjsgProvider",
    "TjspEprocJurisprudenciaProvider",
    "TjspEsajCpopgProvider",
    "TjspNugepnacProvider",
    "TjrsSolrProvider",
    "TjscEprocJurisprudenciaProvider",
    "TcuJurisprudenciaProvider",
    "TreSpTemasProvider",
    "TnuEprocJurisprudenciaProvider",
    "Trf2EprocJurisprudenciaProvider",
    "Trf4EprocJurisprudenciaProvider",
    "Trf5JurisprudenciaProvider",
    "Trf6EprocJurisprudenciaProvider",
]
