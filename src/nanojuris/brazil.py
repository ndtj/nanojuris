"""Brazilian judiciary catalog helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

CourtBranch = Literal[
    "constitutional",
    "superior",
    "federal",
    "state",
    "labor",
    "electoral",
    "military",
    "national_council",
]

ImplementationStatus = Literal["implemented", "planned"]
SourceSystem = Literal[
    "bnp_pangea",
    "datajud",
    "esaj_cjsg",
    "eproc",
    "eproc_jurisprudencia",
    "pje",
    "portal_proprio",
    "projudi_jurisprudencia",
]


@dataclass(slots=True, frozen=True)
class CourtInfo:
    """Stable metadata for a Brazilian judiciary body."""

    code: str
    name: str
    branch: CourtBranch
    jurisdiction: str
    state: str | None = None
    region: str | None = None
    official_url: str | None = None
    source_system: SourceSystem | None = None
    provider_status: ImplementationStatus = "planned"
    providers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalize_court_code(code: str) -> str:
    """Normalize a Brazilian court acronym."""

    return "".join(code.strip().upper().replace("-", " ").split())


def get_court(code: str) -> CourtInfo:
    """Return one court by normalized acronym."""

    normalized = normalize_court_code(code)
    try:
        return _COURTS_BY_CODE[normalized]
    except KeyError as exc:
        raise KeyError(f"Unknown Brazilian court code: {code!r}") from exc


def list_courts(
    *,
    branch: CourtBranch | None = None,
    state: str | None = None,
    source_system: SourceSystem | None = None,
    implemented: bool | None = None,
) -> list[CourtInfo]:
    """List Brazilian judiciary bodies known by NanoJuris."""

    normalized_state = state.strip().upper() if state else None
    courts = list(COURTS)
    if branch:
        courts = [court for court in courts if court.branch == branch]
    if normalized_state:
        courts = [court for court in courts if court.state == normalized_state]
    if source_system:
        courts = [court for court in courts if court.source_system == source_system]
    if implemented is not None:
        expected = "implemented" if implemented else "planned"
        courts = [court for court in courts if court.provider_status == expected]
    return courts


_CORE_COURTS = [
    CourtInfo(
        "CNJ",
        "Conselho Nacional de Justica",
        "national_council",
        "national",
        official_url="https://www.cnj.jus.br/sistemas/datajud/",
        source_system="datajud",
    ),
    CourtInfo(
        "STF",
        "Supremo Tribunal Federal",
        "constitutional",
        "national",
        official_url="https://portal.stf.jus.br/",
        source_system="portal_proprio",
        provider_status="implemented",
        providers=("stf_juris",),
    ),
    CourtInfo(
        "STJ",
        "Superior Tribunal de Justica",
        "superior",
        "national",
        official_url="https://www.stj.jus.br/sites/portalp/Inicio",
        source_system="portal_proprio",
        provider_status="implemented",
        providers=("stj_scon",),
    ),
    CourtInfo(
        "TST",
        "Tribunal Superior do Trabalho",
        "labor",
        "national",
        official_url="https://www.tst.jus.br/",
        source_system="portal_proprio",
        provider_status="implemented",
        providers=("tst_jurisprudencia",),
    ),
    CourtInfo(
        "TSE",
        "Tribunal Superior Eleitoral",
        "electoral",
        "national",
        official_url="https://www.tse.jus.br/",
        source_system="portal_proprio",
    ),
    CourtInfo(
        "STM",
        "Superior Tribunal Militar",
        "military",
        "national",
        official_url="https://www.stm.jus.br/",
        source_system="portal_proprio",
        provider_status="implemented",
        providers=("stm_jurisprudencia",),
    ),
    CourtInfo(
        "TNU",
        "Turma Nacional de Uniformizacao",
        "federal",
        "national",
        official_url="https://www.cjf.jus.br/",
        source_system="eproc_jurisprudencia",
        provider_status="implemented",
        providers=("tnu_eproc_jurisprudencia",),
    ),
]

_FEDERAL_COURTS = [
    CourtInfo(
        "TRF1",
        "Tribunal Regional Federal da 1a Regiao",
        "federal",
        "regional",
        region="1",
        official_url="https://portal.trf1.jus.br/",
    ),
    CourtInfo(
        "TRF2",
        "Tribunal Regional Federal da 2a Regiao",
        "federal",
        "regional",
        region="2",
        official_url="https://www.trf2.jus.br/",
        source_system="eproc_jurisprudencia",
        provider_status="implemented",
        providers=("trf2_eproc_jurisprudencia",),
    ),
    CourtInfo(
        "TRF3",
        "Tribunal Regional Federal da 3a Regiao",
        "federal",
        "regional",
        region="3",
        official_url="https://www.trf3.jus.br/",
    ),
    CourtInfo(
        "TRF4",
        "Tribunal Regional Federal da 4a Regiao",
        "federal",
        "regional",
        region="4",
        official_url="https://www.trf4.jus.br/",
        source_system="eproc",
        provider_status="implemented",
        providers=("trf4_eproc_jurisprudencia",),
    ),
    CourtInfo(
        "TRF5",
        "Tribunal Regional Federal da 5a Regiao",
        "federal",
        "regional",
        region="5",
        official_url="https://www.trf5.jus.br/",
    ),
    CourtInfo(
        "TRF6",
        "Tribunal Regional Federal da 6a Regiao",
        "federal",
        "regional",
        region="6",
        official_url="https://portal.trf6.jus.br/",
        source_system="eproc_jurisprudencia",
        provider_status="implemented",
        providers=("trf6_eproc_jurisprudencia",),
    ),
]

_STATE_COURTS = [
    CourtInfo(
        "TJAC",
        "Tribunal de Justica do Acre",
        "state",
        "state",
        state="AC",
        official_url="https://www.tjac.jus.br/",
        source_system="esaj_cjsg",
        provider_status="implemented",
        providers=("tjac_cjsg",),
    ),
    CourtInfo(
        "TJAL",
        "Tribunal de Justica de Alagoas",
        "state",
        "state",
        state="AL",
        official_url="https://www.tjal.jus.br/",
        source_system="esaj_cjsg",
        provider_status="implemented",
        providers=("tjal_cjsg",),
    ),
    CourtInfo(
        "TJAM",
        "Tribunal de Justica do Amazonas",
        "state",
        "state",
        state="AM",
        official_url="https://www.tjam.jus.br/",
        source_system="esaj_cjsg",
        provider_status="implemented",
        providers=("tjam_cjsg",),
    ),
    CourtInfo(
        "TJAP",
        "Tribunal de Justica do Amapa",
        "state",
        "state",
        state="AP",
        official_url="https://www.tjap.jus.br/",
    ),
    CourtInfo(
        "TJBA",
        "Tribunal de Justica da Bahia",
        "state",
        "state",
        state="BA",
        official_url="https://www.tjba.jus.br/",
    ),
    CourtInfo(
        "TJCE",
        "Tribunal de Justica do Ceara",
        "state",
        "state",
        state="CE",
        official_url="https://www.tjce.jus.br/",
    ),
    CourtInfo(
        "TJDFT",
        "Tribunal de Justica do Distrito Federal e Territorios",
        "state",
        "state",
        state="DF",
        official_url="https://www.tjdft.jus.br/",
        source_system="portal_proprio",
        provider_status="implemented",
        providers=("tjdf_juris",),
    ),
    CourtInfo(
        "TJES",
        "Tribunal de Justica do Espirito Santo",
        "state",
        "state",
        state="ES",
        official_url="https://www.tjes.jus.br/",
    ),
    CourtInfo(
        "TJGO",
        "Tribunal de Justica de Goias",
        "state",
        "state",
        state="GO",
        official_url="https://www.tjgo.jus.br/",
        source_system="projudi_jurisprudencia",
        provider_status="implemented",
        providers=("tjgo_projudi_jurisprudencia",),
    ),
    CourtInfo(
        "TJMA",
        "Tribunal de Justica do Maranhao",
        "state",
        "state",
        state="MA",
        official_url="https://www.tjma.jus.br/",
    ),
    CourtInfo(
        "TJMG",
        "Tribunal de Justica de Minas Gerais",
        "state",
        "state",
        state="MG",
        official_url="https://www.tjmg.jus.br/",
    ),
    CourtInfo(
        "TJMS",
        "Tribunal de Justica de Mato Grosso do Sul",
        "state",
        "state",
        state="MS",
        official_url="https://www.tjms.jus.br/",
        source_system="esaj_cjsg",
        provider_status="implemented",
        providers=("tjms_cjsg",),
    ),
    CourtInfo(
        "TJMT",
        "Tribunal de Justica de Mato Grosso",
        "state",
        "state",
        state="MT",
        official_url="https://www.tjmt.jus.br/",
    ),
    CourtInfo(
        "TJPA",
        "Tribunal de Justica do Para",
        "state",
        "state",
        state="PA",
        official_url="https://www.tjpa.jus.br/",
    ),
    CourtInfo(
        "TJPB",
        "Tribunal de Justica da Paraiba",
        "state",
        "state",
        state="PB",
        official_url="https://www.tjpb.jus.br/",
    ),
    CourtInfo(
        "TJPE",
        "Tribunal de Justica de Pernambuco",
        "state",
        "state",
        state="PE",
        official_url="https://www.tjpe.jus.br/",
    ),
    CourtInfo(
        "TJPI",
        "Tribunal de Justica do Piaui",
        "state",
        "state",
        state="PI",
        official_url="https://www.tjpi.jus.br/",
        source_system="portal_proprio",
        provider_status="implemented",
        providers=("tjpi_juspi",),
    ),
    CourtInfo(
        "TJPR",
        "Tribunal de Justica do Parana",
        "state",
        "state",
        state="PR",
        official_url="https://www.tjpr.jus.br/",
    ),
    CourtInfo(
        "TJRJ",
        "Tribunal de Justica do Rio de Janeiro",
        "state",
        "state",
        state="RJ",
        official_url="https://www.tjrj.jus.br/",
    ),
    CourtInfo(
        "TJRN",
        "Tribunal de Justica do Rio Grande do Norte",
        "state",
        "state",
        state="RN",
        official_url="https://www.tjrn.jus.br/",
    ),
    CourtInfo(
        "TJRO",
        "Tribunal de Justica de Rondonia",
        "state",
        "state",
        state="RO",
        official_url="https://www.tjro.jus.br/",
    ),
    CourtInfo(
        "TJRR",
        "Tribunal de Justica de Roraima",
        "state",
        "state",
        state="RR",
        official_url="https://www.tjrr.jus.br/",
        provider_status="implemented",
        providers=("tjrr_juris",),
    ),
    CourtInfo(
        "TJRS",
        "Tribunal de Justica do Rio Grande do Sul",
        "state",
        "state",
        state="RS",
        official_url="https://www.tjrs.jus.br/",
    ),
    CourtInfo(
        "TJSC",
        "Tribunal de Justica de Santa Catarina",
        "state",
        "state",
        state="SC",
        official_url="https://www.tjsc.jus.br/",
    ),
    CourtInfo(
        "TJSE",
        "Tribunal de Justica de Sergipe",
        "state",
        "state",
        state="SE",
        official_url="https://www.tjse.jus.br/",
    ),
    CourtInfo(
        "TJSP",
        "Tribunal de Justica de Sao Paulo",
        "state",
        "state",
        state="SP",
        official_url="https://www.tjsp.jus.br/",
        source_system="esaj_cjsg",
        provider_status="implemented",
        providers=("tjsp_cjsg", "tjsp_eproc_jurisprudencia", "tjsp_esaj_cpopg"),
    ),
    CourtInfo(
        "TJTO",
        "Tribunal de Justica do Tocantins",
        "state",
        "state",
        state="TO",
        official_url="https://www.tjto.jus.br/",
    ),
]

_LABOR_COURTS = [
    CourtInfo(
        f"TRT{index}",
        f"Tribunal Regional do Trabalho da {index}a Regiao",
        "labor",
        "regional",
        region=str(index),
    )
    for index in range(1, 25)
]

COURTS: tuple[CourtInfo, ...] = tuple(
    sorted(
        [*_CORE_COURTS, *_FEDERAL_COURTS, *_STATE_COURTS, *_LABOR_COURTS],
        key=lambda court: court.code,
    )
)

_COURTS_BY_CODE = {court.code: court for court in COURTS}
