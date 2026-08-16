# Maturity Score

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

O score traduz a maturidade tecnica de cada fonte em uma escala de 0 a 100.
Ele nao substitui revisao humana, mas cria uma fila objetiva para engenharia,
documentacao, QA, Studio, MCP e jurimetria.

## Dimensoes

| Dimensao | Peso | O que mede |
| --- | ---: | --- |
| Entrada | 20 | texto, filtros, paginacao e catalogos |
| Saida | 25 | registros canonicos, campos juridicos, datas, trace e inteiro teor |
| Confiabilidade | 20 | nivel de contrato, risco, live validation e bloqueios |
| Documentacao | 20 | dossie, lacunas, pendencias e fixtures |
| Produto/Jurimetria | 15 | busca unificada, MCP, Studio, CLI e dataset-ready |

## Matriz

| Fonte | Total | Entrada | Saida | Confiabilidade | Docs | Produto | Grau |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `tjdf_juris` | 94 | 17 | 25 | 18 | 19 | 15 | `A` |
| `tjba_graphql` | 90 | 19 | 25 | 16 | 15 | 15 | `A` |
| `tnu_eproc_jurisprudencia` | 90 | 16 | 25 | 18 | 16 | 15 | `A` |
| `tst_jurisprudencia` | 90 | 19 | 25 | 16 | 15 | 15 | `A` |
| `tjpr_jurisprudencia` | 89 | 16 | 22 | 16 | 20 | 15 | `A` |
| `tjrs_solr` | 89 | 16 | 22 | 16 | 20 | 15 | `A` |
| `tjsc_eproc_jurisprudencia` | 89 | 16 | 25 | 14 | 19 | 15 | `A` |
| `trf2_eproc_jurisprudencia` | 89 | 16 | 25 | 18 | 15 | 15 | `A` |
| `trf6_eproc_jurisprudencia` | 89 | 16 | 25 | 18 | 15 | 15 | `A` |
| `tjce_sjuris` | 87 | 16 | 25 | 14 | 17 | 15 | `A` |
| `tjpa_jurisprudencia_bff` | 87 | 19 | 25 | 16 | 12 | 15 | `A` |
| `tjpb_pje_jurisprudencia` | 87 | 19 | 25 | 16 | 12 | 15 | `A` |
| `tjmt_jurisprudencia_api` | 86 | 15 | 25 | 14 | 17 | 15 | `A` |
| `tjto_jurisprudencia` | 86 | 17 | 25 | 12 | 17 | 15 | `A` |
| `tjpe_jurisprudencia` | 84 | 16 | 25 | 11 | 17 | 15 | `B` |
| `tjrr_juris` | 84 | 16 | 25 | 14 | 14 | 15 | `B` |
| `tjpi_juspi` | 83 | 14 | 25 | 16 | 13 | 15 | `B` |
| `tjrj_eproc_jurisprudencia` | 82 | 16 | 25 | 14 | 12 | 15 | `B` |
| `stj_informativo` | 81 | 14 | 22 | 16 | 14 | 15 | `B` |
| `tjac_cjsg` | 80 | 16 | 25 | 12 | 12 | 15 | `B` |
| `tjal_cjsg` | 80 | 16 | 25 | 12 | 12 | 15 | `B` |
| `tjms_cjsg` | 80 | 16 | 25 | 12 | 12 | 15 | `B` |
| `trf4_eproc_jurisprudencia` | 80 | 10 | 25 | 18 | 12 | 15 | `B` |
| `trf5_jurisprudencia` | 80 | 11 | 25 | 14 | 15 | 15 | `B` |
| `stf_informativo` | 78 | 12 | 22 | 16 | 13 | 15 | `B` |
| `stj_scon` | 78 | 10 | 25 | 12 | 16 | 15 | `B` |
| `tjam_cjsg` | 78 | 16 | 25 | 10 | 12 | 15 | `B` |
| `tjce_informativos` | 77 | 18 | 22 | 12 | 10 | 15 | `B` |
| `tjsp_eproc_jurisprudencia` | 76 | 12 | 25 | 12 | 12 | 15 | `B` |
| `tjce_cjsg` | 75 | 16 | 25 | 10 | 9 | 15 | `B` |
| `tjgo_projudi_jurisprudencia` | 75 | 14 | 22 | 10 | 14 | 15 | `B` |
| `tjsp_cjsg` | 75 | 10 | 25 | 10 | 15 | 15 | `B` |
| `stm_jurisprudencia` | 74 | 14 | 25 | 12 | 8 | 15 | `B` |
| `tjro_liame` | 74 | 18 | 19 | 14 | 17 | 6 | `B` |
| `bnp_pangea` | 73 | 16 | 22 | 12 | 8 | 15 | `B` |
| `cjf_jurisprudencia` | 73 | 10 | 22 | 11 | 15 | 15 | `B` |
| `stf_juris` | 73 | 12 | 22 | 10 | 14 | 15 | `B` |
| `cnj_jurisprudencia` | 69 | 17 | 18 | 12 | 10 | 12 | `C` |
| `tcu_jurisprudencia` | 65 | 12 | 14 | 14 | 13 | 12 | `C` |
| `tjsp_nugepnac` | 60 | 12 | 15 | 12 | 9 | 12 | `C` |
| `tre_sp_temas` | 56 | 12 | 11 | 12 | 9 | 12 | `C` |
| `tjma_jurisconsult` | 54 | 8 | 11 | 12 | 17 | 6 | `C` |
| `tce_sp_jurisprudencia` | 52 | 12 | 6 | 10 | 12 | 12 | `C` |
| `stj_dados_abertos_jurisprudencia` | 47 | 10 | 9 | 12 | 12 | 4 | `D` |
| `eproc_jurisprudencia_federal` | 17 | 0 | 0 | 2 | 15 | 0 | `D` |
| `falcao_jt` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjap_tucujuris` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjes_jurisprudencia` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjmg_jurisprudencia` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjrn_jurisprudencia` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjse_jurisprudencia` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `justica_eleitoral_sjur` | 11 | 0 | 0 | 2 | 9 | 0 | `D` |
| `trf3_jurisprudencia` | 11 | 0 | 0 | 2 | 9 | 0 | `D` |
| `trt2_pje_jurisprudencia` | 11 | 0 | 0 | 2 | 9 | 0 | `D` |

## Como Interpretar

- `A`: referencia para demonstracao, Studio, MCP e coletas iniciais.
- `B`: util, mas ainda precisa fechar lacunas antes de virar referencia nacional.
- `C`: provider promissor, adequado para hardening e testes de contrato.
- `D`: fonte mapeada ou contextual; nao deve liderar jurimetria ampla.

Uma fonte de alto valor juridico pode ter score baixo se o acesso live, a
paginacao, os filtros ou a documentacao ainda nao estiverem maduros.
