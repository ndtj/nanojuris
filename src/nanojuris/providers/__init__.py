"""Provider implementations."""

from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.providers.bnp_pangea import BnpPangeaProvider
from nanojuris.providers.cjf_jurisprudencia import CjfJurisprudenciaProvider
from nanojuris.providers.eproc_jurisprudencia_federal import (
    FederalEprocJurisprudenciaFamilyProvider,
    FederalEprocJurisprudenciaProvider,
)
from nanojuris.providers.falcao_jt import FalcaoJtProvider
from nanojuris.providers.stf_juris import StfJurisProvider
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
from nanojuris.providers.tjce_cjsg import TjceCjsgProvider
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
from nanojuris.providers.tjms_cjpg import TjmsCjpgProvider
from nanojuris.providers.tjms_cjsg import TjmsCjsgProvider
from nanojuris.providers.tjmsp_jurisprudencia import TjmspJurisprudenciaProvider
from nanojuris.providers.tjmt_jurisprudencia_api import TjmtJurisprudenciaApiProvider
from nanojuris.providers.tjpa_jurisprudencia_bff import TjpaJurisprudenciaBffProvider
from nanojuris.providers.tjpb_pje_jurisprudencia import TjpbPjeJurisprudenciaProvider
from nanojuris.providers.tjrj_banco_sentencas import TjrjBancoSentencasProvider
from nanojuris.providers.tjrj_ejuris import TjrjEjurisProvider
from nanojuris.providers.tjrj_eproc_jurisprudencia import TjrjEprocJurisprudenciaProvider
from nanojuris.providers.tjrn_jurisprudencia import TjrnJurisprudenciaProvider
from nanojuris.providers.tjro_jurisprudencia import TjroJurisprudenciaProvider
from nanojuris.providers.tjro_liame import TjroLiameProvider
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
    TRE_STATES,
    TreSjurJurisprudenciaFamilyProvider,
    TreSjurJurisprudenciaProvider,
    TseSjurJurisprudenciaProvider,
)

__all__ = [
    "BnpPangeaProvider",
    "CjfJurisprudenciaProvider",
    "FederalEprocJurisprudenciaProvider",
    "FederalEprocJurisprudenciaFamilyProvider",
    "FalcaoJtProvider",
    "JurisprudenceProvider",
    "StfJurisProvider",
    "StjSconProvider",
    "StmJurisprudenciaProvider",
    "TceSpJurisprudenciaProvider",
    "TcePrViaJurisProvider",
    "TjacCjsgProvider",
    "TjacEmentarioJurisprudenciaProvider",
    "TjceCjsgProvider",
    "TjceSjurisProvider",
    "TjdfJurisProvider",
    "TjgoProjudiJurisprudenciaProvider",
    "TjpaJurisprudenciaBffProvider",
    "TjpbPjeJurisprudenciaProvider",
    "TjrjEprocJurisprudenciaProvider",
    "TjrjEjurisProvider",
    "TjrjBancoSentencasProvider",
    "TjalCjsgProvider",
    "TjalTurmaRecursalEmentarioProvider",
    "TjalEsmalBancoSentencasProvider",
    "TjamCjsgProvider",
    "TjmsCjsgProvider",
    "TjmsCjpgProvider",
    "TjmtJurisprudenciaApiProvider",
    "TjesCjpgProvider",
    "TjesJurisprudenciaProvider",
    "TjesTurmaRecursalProvider",
    "TjmaJurisconsultProvider",
    "TjmaInformativosProvider",
    "TjmgJurisprudenciaProvider",
    "TjmmgJurisprudenciaApiProvider",
    "TjmspJurisprudenciaProvider",
    "TjmgDspaceJurisprudenciaProvider",
    "TjmgEjefBoletimJurisprudenciaProvider",
    "TjapTucujurisProvider",
    "TjapBancoSentencasProvider",
    "TjacBancoSentencasProvider",
    "TjspCjsgProvider",
    "TjspCjpgProvider",
    "TjspEprocJurisprudenciaProvider",
    "TjspNugepnacProvider",
    "TjtoJurisprudenciaProvider",
    "TjrsSolrProvider",
    "TjroLiameProvider",
    "TjroJurisprudenciaProvider",
    "TjrnJurisprudenciaProvider",
    "TjscEprocJurisprudenciaProvider",
    "TjseJurisprudenciaProvider",
    "TjseBoletimJurisprudenciaProvider",
    "TreSjurJurisprudenciaFamilyProvider",
    "TreSjurJurisprudenciaProvider",
    "TreSjurFirstDegreeFamilyProvider",
    "TreSjurFirstDegreeProvider",
    "TseSjurJurisprudenciaProvider",
    "TRE_AUTHORITIES",
    "TRE_STATES",
    "TcuJurisprudenciaProvider",
    "TreSpTemasProvider",
    "TnuEprocJurisprudenciaProvider",
    "Trf2EprocJurisprudenciaProvider",
    "Trf4EprocJurisprudenciaProvider",
    "Trf5JurisprudenciaProvider",
    "Trf3JurisprudenciaProvider",
    "Trf6EprocJurisprudenciaProvider",
    "Trt2BasisJurisprudenciaProvider",
    "Trt2EmentarioJurisprudenciaProvider",
    "Trt2PjeJurisprudenciaProvider",
    "Trt3EmentarioJurisprudenciaProvider",
    "Trt9NugepnacJurisprudenciaProvider",
    "Trt4SumulasJurisprudenciaProvider",
    "Trt15JurisprudenciaProvider",
    "Trt6JurisprudenciaProvider",
    "Trt8PjeJurisprudenciaProvider",
]
