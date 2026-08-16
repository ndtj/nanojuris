"""Provider contract maturity inventory for NanoJuris sources."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from nanojuris.models import ProviderCapabilities


@dataclass(frozen=True, slots=True)
class SourceContractAssessment:
    """Operational maturity assessment for one public source contract."""

    source: str
    display_name: str
    category: str
    contract_level: int
    contract_label: str
    maturity: str
    source_family: str
    strengths: list[str]
    gaps: list[str]
    next_steps: list[str]
    mcp_recommendation: str
    jurimetry_fit: str
    risk_level: str
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CONTRACT_LEVEL_LABELS = {
    1: "busca_basica",
    2: "parser_com_fixtures",
    3: "contrato_http_documentado",
    4: "campos_canonicos_estaveis",
    5: "erros_e_vazios_mapeados",
    6: "pronto_para_agentes",
}


SOURCE_OVERRIDES: dict[str, dict[str, Any]] = {
    "bnp_pangea": {
        "contract_level": 4,
        "source_family": "api_publica_precedentes",
        "mcp_recommendation": (
            "Use para precedentes qualificados; evite tratar como jurisprudencia comum."
        ),
        "jurimetry_fit": "alto para teses qualificadas; medio para pesquisa livre.",
        "risk_level": "medio",
        "gaps": [
            (
                "Expandir a matriz de rejeicoes HTTP 400 por tribunal, especie e "
                "combinacao de filtros."
            ),
            "Documentar payload completo de filtros e agregacoes.",
            "Cobrir heuristica de sugestoes/catalogo para consultas curtas.",
        ],
    },
    "stf_juris": {
        "contract_level": 4,
        "source_family": "api_json_jurisprudencia_superior",
        "mcp_recommendation": ("Use quando a API responder JSON; reporte AWS WAF/SSL sem bypass."),
        "jurimetry_fit": "alto para acordaos constitucionais quando o acesso estiver estavel.",
        "risk_level": "alto",
        "gaps": [
            "Separar AWS WAF challenge, falha SSL local e ausencia de resultados.",
            "Validar bases adicionais do frontend: decisoes, sumulas, informativos e noticias.",
            "Promover inteiro teor do portal STF somente quando responder sem 403 em sessao limpa.",
        ],
    },
    "stf_informativo": {
        "contract_level": 5,
        "source_family": "xlsx_jurisprudencia_curada_superior",
        "mcp_recommendation": (
            "Use como fonte STF preferencial para teses/resumos oficiais quando a API JSON "
            "de jurisprudencia estiver sob WAF."
        ),
        "jurimetry_fit": "alto para estudos tematicos de teses oficiais e materias do STF.",
        "risk_level": "baixo",
        "gaps": [
            "Adicionar amostras reais por ramo do direito e repercussao geral.",
            "Versionar dicionario de colunas quando o STF alterar a planilha.",
        ],
    },
    "stj_informativo": {
        "contract_level": 5,
        "source_family": "html_jurisprudencia_curada_superior",
        "mcp_recommendation": (
            "Use para notas oficiais do STJ; complemente com SCON quando acordao integral "
            "estiver acessivel sem validacao."
        ),
        "jurimetry_fit": (
            "alto para estudos de teses e informativos oficiais; limitado para corpus integral."
        ),
        "risk_level": "medio",
        "gaps": [
            "Adicionar fixtures de multiplas notas, zero resultado e links CNOT.",
            "Mapear filtros oficiais por ramo, orgao julgador e ministro.",
        ],
    },
    "tjba_graphql": {
        "contract_level": 5,
        "source_family": "api_graphql_jurisprudencia_tribunal",
        "mcp_recommendation": (
            "Use para busca textual e inteiro teor HTML publico; preserve o hash UUID "
            "e o trace de cada documento."
        ),
        "jurimetry_fit": "alto para pesquisa textual estadual com documento publico.",
        "risk_level": "medio",
        "gaps": [
            "Monitorar mudancas no schema GraphQL e nos catalogos de filtros.",
            "Expandir a amostra live de pagina vazia e paginas posteriores.",
        ],
    },
    "tjrs_solr": {
        "contract_level": 5,
        "source_family": "api_ajax_solr_jurisprudencia_tribunal",
        "mcp_recommendation": (
            "Use para pesquisa textual e facetas do TJRS; nao anuncie detalhe ou inteiro "
            "teor ate que uma rota publica seja reproduzida."
        ),
        "jurimetry_fit": "alto para busca textual e contagens do indice, com limites documentados.",
        "risk_level": "medio",
        "gaps": [
            "Validar pagina vazia e pagina posterior em monitoramento live controlado.",
            "Mapear rotas publicas de detalhe e inteiro teor antes de anuncia-las.",
        ],
    },
    "tjrr_juris": {
        "contract_level": 5,
        "source_family": "jsf_primefaces_jurisprudencia_tribunal",
        "mcp_recommendation": (
            "Use com baixa frequencia para busca publica TJRR; preserve a sessao JSF, "
            "a janela efetiva e o detalhe por id observado."
        ),
        "jurimetry_fit": "alto para estudos estaduais quando a sessao publica estiver estavel.",
        "risk_level": "medio",
        "gaps": [
            "Ampliar live controlado para vazio, estado expirado e detalhe.",
            "Monitorar nomes dinamicos de campos JSF e limites PrimeFaces.",
        ],
    },
    "tjpr_jurisprudencia": {
        "contract_level": 5,
        "source_family": "html_form_jurisprudencia_tribunal",
        "mcp_recommendation": (
            "Use para busca textual e ementas publicas do TJPR; trate links de detalhe "
            "como disponiveis, nao como inteiro teor carregado."
        ),
        "jurimetry_fit": "alto para pesquisa textual estadual com ementa e metadados.",
        "risk_level": "medio",
        "gaps": [
            "Ampliar fixtures por filtros e estados de conteudo pendente.",
            "Validar se a rota de detalhe pode ser carregada por URL preservada.",
        ],
    },
    "tjpa_jurisprudencia_bff": {
        "contract_level": 5,
        "source_family": "api_json_bff_jurisprudencia_tribunal",
        "mcp_recommendation": (
            "Use para busca textual TJPA, preservando o limite tecnico e distinguindo "
            "texto integral embutido de documento separado."
        ),
        "jurimetry_fit": "alto para analise textual estadual, com limite tecnico declarado.",
        "risk_level": "medio",
        "gaps": [
            "Completar fixtures de filtros, vazio e erro do BFF.",
            "Validar uma rota publica de detalhe antes de anuncia-la.",
        ],
    },
    "tjpb_pje_jurisprudencia": {
        "contract_level": 5,
        "source_family": "api_json_pje_jurisprudencia_tribunal",
        "mcp_recommendation": (
            "Use quando a sessao publica fornecer token e busca JSON; preserve o "
            "documento HTML observado e diagnostique desafios sem bypass."
        ),
        "jurimetry_fit": "alto para pesquisa textual estadual com documento publico sob demanda.",
        "risk_level": "medio",
        "gaps": [
            "Ampliar fixtures de token, vazio e desafio de acesso.",
            "Validar live o detalhe HTML com identificador da busca em baixa frequencia.",
        ],
    },
    "tjpi_juspi": {
        "contract_level": 5,
        "source_family": "html_jurisprudencia_tribunal",
        "mcp_recommendation": (
            "Use para pesquisa textual e detalhe HTML publico do TJPI/JusPI, "
            "preservando public_id, paginacao e trace."
        ),
        "jurimetry_fit": "alto para estudos estaduais com busca paginada e documento publico.",
        "risk_level": "medio",
        "gaps": [
            "Adicionar validacao live opt-in de detalhe e pagina posterior.",
            "Catalogar valores textuais dos filtros publicados no formulario.",
        ],
    },
    "stj_scon": {
        "contract_level": 4,
        "source_family": "html_jurisprudencia_superior",
        "mcp_recommendation": (
            "Use com page_size pequeno e reporte verificacao automatica sem bypass."
        ),
        "jurimetry_fit": "alto quando o contrato de acesso estiver estabilizado.",
        "risk_level": "alto",
        "gaps": [
            "Separar acesso bloqueado por verificacao automatica de ausencia de resultados.",
            "Validar URL publica de inteiro teor em sessao limpa sem cookies.",
            "Promover fixtures de monocraticas, sumulas e informativos.",
        ],
    },
    "stm_jurisprudencia": {
        "contract_level": 4,
        "source_family": "html_jurisprudencia_eproc",
        "mcp_recommendation": "Use com termos especificos e page_size pequeno.",
        "jurimetry_fit": "medio para estudos setoriais de direito penal/militar.",
        "risk_level": "medio",
        "gaps": [
            "Documentar paginacao remota e facetas se forem estaveis.",
            "Adicionar fixtures de pagina vazia, pagina com multiplos resultados e inteiro teor.",
            "Mapear variacoes de labels acentuados no HTML.",
        ],
    },
    "tst_jurisprudencia": {
        "contract_level": 5,
        "source_family": "api_json_jurisprudencia_trabalhista",
        "mcp_recommendation": (
            "Use para pesquisa textual e inteiro teor publico da jurisprudencia trabalhista do TST."
        ),
        "jurimetry_fit": (
            "alto para estudos de jurisprudencia trabalhista, filtros e series temporais."
        ),
        "risk_level": "medio",
        "gaps": [
            "Consultar config.json quando a base da API for alterada pelo frontend.",
            "Ampliar fixtures por sumulas, precedentes normativos e filtros de catalogo.",
            "Monitorar alteracoes no HTML de inteiro teor e nos campos removidos do backend.",
        ],
    },
    "tjdf_juris": {
        "contract_level": 5,
        "source_family": "html_jurisprudencia_tribunal",
        "mcp_recommendation": "Boa fonte para demonstracoes e estudos jurimetricos iniciais.",
        "jurimetry_fit": "alto para pesquisas textuais com metadados e detalhe.",
        "risk_level": "baixo",
        "gaps": [
            "Completar dossie de parametros de detalhe e ordenacao.",
            "Criar fixtures para zero resultado e mudancas de detalhe.",
        ],
    },
    "tjsp_cjsg": {
        "contract_level": 4,
        "source_family": "html_esaj_cjsg",
        "mcp_recommendation": (
            "Use quando a fonte publica nao exigir captcha; reporte bloqueio sem bypass."
        ),
        "jurimetry_fit": "alto em relevancia, medio em confiabilidade operacional.",
        "risk_level": "alto",
        "gaps": [
            "Documentar criterios objetivos de captcha/access-control.",
            "Separar rotas de pesquisa, detalhe e inteiro teor.",
            "Aprofundar fixtures por classe, orgao julgador e documento indisponivel.",
        ],
    },
    "tjsp_eproc_jurisprudencia": {
        "contract_level": 4,
        "source_family": "html_jurisprudencia_eproc",
        "mcp_recommendation": "Use para jurisprudencia eproc/TJSP com filtros de origem.",
        "jurimetry_fit": "medio-alto para estudos recentes.",
        "risk_level": "medio",
        "gaps": [
            "Aprofundar contrato de source_origin.",
            "Validar estrategia de inteiro teor/documentos quando disponivel.",
            "Documentar limites por primeiro grau, segundo grau e colegio recursal.",
        ],
    },
    "tnu_eproc_jurisprudencia": {
        "contract_level": 5,
        "source_family": "html_jurisprudencia_eproc",
        "mcp_recommendation": "Use para jurisprudencia federal da TNU por tema ou numero.",
        "jurimetry_fit": "alto para uniformizacao federal e previdenciario.",
        "risk_level": "baixo",
        "gaps": [
            "Validar live a rota de inteiro teor com id_jurisprudencia real.",
            "Adicionar fixtures por tipo decisorio alem de acordaos.",
        ],
    },
    "trf2_eproc_jurisprudencia": {
        "contract_level": 5,
        "source_family": "html_jurisprudencia_eproc",
        "mcp_recommendation": "Use para jurisprudencia federal do TRF2, TRU2 e Turmas Recursais.",
        "jurimetry_fit": "alto para estudos federais regionais.",
        "risk_level": "baixo",
        "gaps": [
            "Validar live a rota de inteiro teor com id_jurisprudencia real.",
            "Aprofundar filtros de origem TRF2, TRU2 e Turmas Recursais.",
        ],
    },
    "trf4_eproc_jurisprudencia": {
        "contract_level": 5,
        "source_family": "html_jurisprudencia_eproc",
        "mcp_recommendation": "Boa fonte para estudos federais e testes de inteiro teor.",
        "jurimetry_fit": "alto para jurisprudencia federal e eproc.",
        "risk_level": "baixo",
        "gaps": [
            "Expandir fixtures por tipo decisorio.",
            "Documentar paginacao, ordenacao e limites de consulta.",
        ],
    },
    "trf6_eproc_jurisprudencia": {
        "contract_level": 5,
        "source_family": "html_jurisprudencia_eproc",
        "mcp_recommendation": (
            "Use para jurisprudencia federal do TRF6, TRU6, Turmas Recursais e Varas Federais."
        ),
        "jurimetry_fit": "alto para estudos federais regionais em Minas Gerais.",
        "risk_level": "baixo",
        "gaps": [
            "Validar live a rota de inteiro teor com id_jurisprudencia real.",
            "Aprofundar filtros de origem TRF6, TRU6, Turmas Recursais e Varas Federais.",
        ],
    },
}

FAMILY_DEFAULTS = {
    "tjac_cjsg": "html_esaj_cjsg",
    "tjal_cjsg": "html_esaj_cjsg",
    "tjam_cjsg": "html_esaj_cjsg",
    "tjms_cjsg": "html_esaj_cjsg",
    "tce_sp_jurisprudencia": "catalogo_administrativo",
    "tjsp_nugepnac": "catalogo_precedentes",
    "tre_sp_temas": "catalogo_tematico_eleitoral",
}


def assess_source_contract(capability: ProviderCapabilities) -> SourceContractAssessment:
    """Assess one provider from declared capabilities and curated knowledge."""

    override = SOURCE_OVERRIDES.get(capability.source, {})
    level = int(override.get("contract_level") or _infer_contract_level(capability))
    strengths = _strengths(capability)
    gaps = list(override.get("gaps") or _default_gaps(capability, level))
    return SourceContractAssessment(
        source=capability.source,
        display_name=capability.display_name,
        category=capability.category,
        contract_level=level,
        contract_label=CONTRACT_LEVEL_LABELS[level],
        maturity=_maturity(level),
        source_family=str(
            override.get("source_family")
            or FAMILY_DEFAULTS.get(capability.source)
            or capability.category
        ),
        strengths=strengths,
        gaps=gaps,
        next_steps=_next_steps(capability, gaps),
        mcp_recommendation=str(
            override.get("mcp_recommendation") or _default_mcp_recommendation(capability)
        ),
        jurimetry_fit=str(override.get("jurimetry_fit") or _default_jurimetry_fit(capability)),
        risk_level=str(override.get("risk_level") or _risk_level(capability, level)),
        evidence={
            "search_modes": capability.search_modes,
            "document_types": capability.document_types,
            "canonical_records": capability.canonical_records,
            "extracted_fields": capability.extracted_fields,
            "endpoints": capability.endpoints,
            "supports_full_text": capability.supports_full_text,
            "supports_catalog": capability.supports_catalog,
            "supports_suggestions": capability.supports_suggestions,
            "supports_live_tests": capability.supports_live_tests,
            "supports_mcp": capability.supports_mcp,
            "pagination_mode": capability.pagination_mode,
            "completeness_contract": capability.completeness_contract,
            "limitations": capability.limitations,
            "responsible_use": capability.responsible_use,
        },
    )


def assess_source_contracts(
    capabilities: list[ProviderCapabilities],
) -> list[SourceContractAssessment]:
    """Assess all providers sorted by source name."""

    return [
        assess_source_contract(item) for item in sorted(capabilities, key=lambda cap: cap.source)
    ]


def summarize_contracts(
    assessments: list[SourceContractAssessment],
) -> dict[str, Any]:
    """Return a compact maturity summary for dashboards, CLI and MCP."""

    by_level: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    for assessment in assessments:
        by_level[str(assessment.contract_level)] = (
            by_level.get(str(assessment.contract_level), 0) + 1
        )
        by_risk[assessment.risk_level] = by_risk.get(assessment.risk_level, 0) + 1

    shallow = [
        item.source
        for item in assessments
        if item.contract_level < 4 or item.risk_level in {"alto", "critico"}
    ]
    ready_for_agents = [
        item.source
        for item in assessments
        if item.contract_level >= 5 and item.risk_level in {"baixo", "medio"}
    ]
    return {
        "total_sources": len(assessments),
        "by_level": by_level,
        "by_risk": by_risk,
        "needs_deepening": shallow,
        "ready_for_agents": ready_for_agents,
    }


def contracts_payload(
    capabilities: list[ProviderCapabilities],
    *,
    source: str = "",
) -> dict[str, Any]:
    """Build a JSON-ready source contract payload."""

    assessments = assess_source_contracts(capabilities)
    if source:
        assessments = [item for item in assessments if item.source == source]
    return {
        "summary": summarize_contracts(assessments),
        "contracts": [item.to_dict() for item in assessments],
    }


def _infer_contract_level(capability: ProviderCapabilities) -> int:
    level = 1
    if capability.canonical_records and capability.extracted_fields:
        level = 2
    if capability.endpoints and capability.limitations:
        level = 3
    if capability.supports_full_text or capability.supports_catalog:
        level = 4
    if capability.supports_live_tests and capability.responsible_use:
        level = max(level, 4)
    if capability.category == "case_lookup":
        level = min(level, 4)
    return level


def _strengths(capability: ProviderCapabilities) -> list[str]:
    strengths = [
        "Declara capacidades por ProviderCapabilities.",
        f"Categoria operacional: {capability.category}.",
    ]
    if capability.endpoints:
        strengths.append("Possui endpoints/rotas publicas declaradas.")
    if capability.extracted_fields:
        strengths.append("Declara campos extraidos para auditoria.")
    if capability.supports_full_text:
        strengths.append("Suporta algum fluxo de inteiro teor/documento publico.")
    if capability.supports_catalog:
        strengths.append("Expoe catalogo ou parametros publicos.")
    if capability.supports_live_tests:
        strengths.append("Possui teste live opcional para verificacao controlada.")
    return strengths


def _default_gaps(capability: ProviderCapabilities, level: int) -> list[str]:
    gaps: list[str] = []
    if level < 3:
        gaps.append("Documentar contrato HTTP completo com parametros e respostas.")
    if not capability.supports_catalog:
        gaps.append(
            "Registrar como a fonte representa filtros, classes e tipos sem catalogo formal."
        )
    if "date_range" in capability.search_modes:
        gaps.append("Validar formatos de data aceitos e comportamento por intervalo vazio.")
    if capability.supports_full_text:
        gaps.append("Mapear indisponibilidade, hash e tamanho de inteiro teor.")
    if capability.category == "case_lookup":
        gaps.append(
            "Separar claramente consulta processual de jurisprudencia no MCP e na documentacao."
        )
    if not gaps:
        gaps.append(
            "Completar dossie com casos reais publicos, fixtures e criterios de estabilidade."
        )
    return gaps


def _next_steps(capability: ProviderCapabilities, gaps: list[str]) -> list[str]:
    steps = [
        "Criar ou atualizar dossie em docs/providers/<provider>/README.md e manter "
        "a copia de compatibilidade em docs/source-contracts.",
        "Salvar fixtures publicas para sucesso, vazio e erro esperado.",
        "Adicionar teste de parser e teste de contrato de erro.",
    ]
    if capability.supports_full_text:
        steps.append("Validar get_document/get_decisions com documento publico e trace completo.")
    if gaps:
        steps.append(f"Atacar primeiro: {gaps[0]}")
    return steps


def _default_mcp_recommendation(capability: ProviderCapabilities) -> str:
    if capability.category == "case_lookup":
        return "Use apenas quando houver identificador processual, como numero CNJ, parte ou OAB."
    if capability.category == "judicial_communications":
        return "Use para comunicacoes judiciais, nao para jurisprudencia."
    if capability.supports_mcp:
        return "Pode ser exposta no MCP com diagnosticos e limites preservados."
    return "Nao exponha no MCP ate declarar suporte e limites."


def _default_jurimetry_fit(capability: ProviderCapabilities) -> str:
    if capability.category in {"court_jurisprudence", "administrative_jurisprudence"}:
        return "medio; depende da completude de campos, detalhes e inteiro teor."
    if capability.category in {"qualified_precedents", "court_precedents"}:
        return "alto para estudos de precedentes qualificados; limitado para amostras decisorias."
    if capability.category == "case_lookup":
        return "baixo para jurisprudencia; util para contexto processual identificado."
    return "baixo; fonte especializada fora de jurisprudencia decisoria comum."


def _risk_level(capability: ProviderCapabilities, level: int) -> str:
    limitation_text = " ".join(capability.limitations).lower()
    if "captcha" in limitation_text or "controle de acesso" in limitation_text:
        return "alto"
    if level >= 5:
        return "baixo"
    if level >= 3:
        return "medio"
    return "alto"


def _maturity(level: int) -> str:
    if level >= 5:
        return "maduro"
    if level >= 3:
        return "intermediario"
    return "inicial"
