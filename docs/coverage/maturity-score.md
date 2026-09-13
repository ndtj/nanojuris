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
| `tjpb_pje_jurisprudencia` | 95 | 19 | 25 | 16 | 20 | 15 | `A` |
| `tnu_eproc_jurisprudencia` | 95 | 17 | 25 | 18 | 20 | 15 | `A` |
| `tjba_graphql` | 94 | 19 | 25 | 16 | 19 | 15 | `A` |
| `tjdf_juris` | 94 | 17 | 25 | 18 | 19 | 15 | `A` |
| `tjpa_jurisprudencia_bff` | 94 | 18 | 25 | 16 | 20 | 15 | `A` |
| `trf2_eproc_jurisprudencia` | 94 | 17 | 25 | 18 | 19 | 15 | `A` |
| `trf6_eproc_jurisprudencia` | 94 | 17 | 25 | 18 | 19 | 15 | `A` |
| `tst_jurisprudencia` | 94 | 19 | 25 | 16 | 19 | 15 | `A` |
| `tjpi_juspi` | 93 | 17 | 25 | 16 | 20 | 15 | `A` |
| `tjpr_jurisprudencia` | 93 | 17 | 25 | 16 | 20 | 15 | `A` |
| `trt2_ementario_jurisprudencia` | 93 | 19 | 25 | 14 | 20 | 15 | `A` |
| `tjrr_juris` | 92 | 17 | 25 | 16 | 19 | 15 | `A` |
| `tjrs_solr` | 92 | 16 | 25 | 16 | 20 | 15 | `A` |
| `trf4_eproc_jurisprudencia` | 92 | 14 | 25 | 18 | 20 | 15 | `A` |
| `tjap_banco_sentencas` | 91 | 17 | 25 | 14 | 20 | 15 | `A` |
| `tjmt_jurisprudencia_api` | 91 | 17 | 25 | 14 | 20 | 15 | `A` |
| `tjpe_jurisprudencia` | 91 | 17 | 25 | 14 | 20 | 15 | `A` |
| `tjrj_ejuris` | 91 | 17 | 25 | 14 | 20 | 15 | `A` |
| `tjrj_eproc_jurisprudencia` | 91 | 17 | 25 | 14 | 20 | 15 | `A` |
| `tjsc_eproc_jurisprudencia` | 91 | 17 | 25 | 14 | 20 | 15 | `A` |
| `tjto_jurisprudencia` | 91 | 17 | 25 | 14 | 20 | 15 | `A` |
| `trt8_pje_jurisprudencia` | 91 | 17 | 25 | 14 | 20 | 15 | `A` |
| `stj_informativo` | 90 | 14 | 25 | 16 | 20 | 15 | `A` |
| `tce_pr_viajuris` | 90 | 17 | 25 | 14 | 19 | 15 | `A` |
| `tjsp_eproc_jurisprudencia` | 90 | 17 | 25 | 14 | 19 | 15 | `A` |
| `tjal_cjsg` | 89 | 17 | 25 | 12 | 20 | 15 | `A` |
| `tjam_cjsg` | 89 | 17 | 25 | 12 | 20 | 15 | `A` |
| `tjce_cjsg` | 89 | 17 | 25 | 12 | 20 | 15 | `A` |
| `tjce_sjuris` | 89 | 16 | 25 | 14 | 19 | 15 | `A` |
| `tjgo_projudi_jurisprudencia` | 89 | 17 | 25 | 12 | 20 | 15 | `A` |
| `tjms_cjsg` | 89 | 17 | 25 | 12 | 20 | 15 | `A` |
| `tjrn_jurisprudencia` | 89 | 17 | 25 | 12 | 20 | 15 | `A` |
| `tjse_boletim_jurisprudencia` | 89 | 17 | 25 | 14 | 20 | 13 | `A` |
| `trf5_jurisprudencia` | 89 | 15 | 25 | 14 | 20 | 15 | `A` |
| `stm_jurisprudencia` | 88 | 14 | 25 | 14 | 20 | 15 | `A` |
| `tcu_jurisprudencia` | 88 | 17 | 22 | 14 | 20 | 15 | `A` |
| `tjac_cjsg` | 88 | 17 | 25 | 12 | 19 | 15 | `A` |
| `tjac_ementario_jurisprudencia` | 88 | 17 | 22 | 14 | 20 | 15 | `A` |
| `tjes_cjpg` | 88 | 16 | 25 | 12 | 20 | 15 | `A` |
| `tjsp_cjsg` | 88 | 16 | 25 | 12 | 20 | 15 | `A` |
| `bnp_pangea` | 87 | 20 | 19 | 14 | 19 | 15 | `A` |
| `tjes_jurisprudencia` | 87 | 15 | 25 | 12 | 20 | 15 | `A` |
| `tjes_turma_recursal` | 87 | 15 | 25 | 12 | 20 | 15 | `A` |
| `tjmg_dspace_jurisprudencia` | 87 | 16 | 25 | 14 | 19 | 13 | `A` |
| `tjmg_jurisprudencia` | 87 | 17 | 25 | 12 | 20 | 13 | `A` |
| `tjms_cjpg` | 87 | 15 | 25 | 12 | 20 | 15 | `A` |
| `tjsp_cjpg` | 87 | 15 | 25 | 12 | 20 | 15 | `A` |
| `tjro_liame` | 85 | 18 | 19 | 14 | 19 | 15 | `A` |
| `trt6_jurisprudencia` | 85 | 17 | 22 | 14 | 19 | 13 | `A` |
| `tjal_esmal_banco_sentencas` | 84 | 17 | 21 | 14 | 20 | 12 | `B` |
| `tjmg_ejef_boletim_jurisprudencia` | 84 | 17 | 21 | 14 | 20 | 12 | `B` |
| `cnj_jurisprudencia` | 83 | 17 | 21 | 14 | 19 | 12 | `B` |
| `tjro_jurisprudencia` | 82 | 16 | 25 | 14 | 20 | 7 | `B` |
| `trt15_jurisprudencia` | 80 | 19 | 25 | 10 | 20 | 6 | `B` |
| `tse_sjur_jurisprudencia` | 78 | 17 | 22 | 14 | 19 | 6 | `B` |
| `tjal_turma_recursal_ementario` | 77 | 17 | 22 | 12 | 20 | 6 | `B` |
| `tjmmg_jurisprudencia_api` | 77 | 17 | 25 | 14 | 17 | 4 | `B` |
| `eproc_jurisprudencia_federal` | 76 | 14 | 25 | 12 | 19 | 6 | `B` |
| `stj_scon` | 75 | 14 | 25 | 10 | 20 | 6 | `B` |
| `tjac_banco_sentencas` | 75 | 17 | 21 | 14 | 17 | 6 | `B` |
| `stj_dados_abertos_jurisprudencia` | 74 | 11 | 25 | 14 | 20 | 4 | `B` |
| `stf_informativo` | 73 | 16 | 22 | 15 | 14 | 6 | `B` |
| `tjrj_banco_sentencas` | 73 | 17 | 21 | 12 | 17 | 6 | `B` |
| `tjsp_nugepnac` | 73 | 16 | 19 | 12 | 20 | 6 | `B` |
| `tjap_tucujuris` | 72 | 19 | 22 | 12 | 15 | 4 | `B` |
| `tjce_informativos` | 70 | 18 | 22 | 14 | 10 | 6 | `B` |
| `tjse_jurisprudencia` | 70 | 19 | 22 | 12 | 13 | 4 | `B` |
| `tre_sjur_first_degree` | 70 | 17 | 22 | 14 | 11 | 6 | `B` |
| `cjf_jurisprudencia` | 69 | 14 | 22 | 12 | 15 | 6 | `C` |
| `stf_juris` | 69 | 17 | 22 | 10 | 14 | 6 | `C` |
| `tjma_informativos` | 68 | 10 | 21 | 14 | 17 | 6 | `C` |
| `falcao_jt` | 67 | 14 | 22 | 12 | 15 | 4 | `C` |
| `trt2_basis_jurisprudencia` | 66 | 17 | 25 | 12 | 8 | 4 | `C` |
| `tce_sp_jurisprudencia` | 65 | 16 | 13 | 10 | 20 | 6 | `C` |
| `tre_sjur_jurisprudencia` | 65 | 17 | 22 | 12 | 8 | 6 | `C` |
| `tjma_jurisconsult` | 63 | 11 | 19 | 10 | 17 | 6 | `C` |
| `trf3_jurisprudencia` | 63 | 9 | 22 | 12 | 14 | 6 | `C` |
| `trt2_pje_jurisprudencia` | 63 | 17 | 19 | 10 | 13 | 4 | `C` |
| `trt3_ementario_jurisprudencia` | 61 | 15 | 18 | 14 | 8 | 6 | `C` |
| `trt4_sumulas_jurisprudencia` | 59 | 15 | 18 | 12 | 8 | 6 | `C` |
| `trt9_nugepnac_jurisprudencia` | 59 | 15 | 18 | 12 | 8 | 6 | `C` |
| `tre_sp_temas` | 58 | 16 | 14 | 11 | 11 | 6 | `C` |
| `tjmrs_jurisprudencia` | 57 | 9 | 18 | 14 | 10 | 6 | `C` |
| `tjmsp_jurisprudencia` | 54 | 12 | 22 | 12 | 4 | 4 | `C` |
| `justica_eleitoral_sjur` | 44 | 6 | 6 | 11 | 15 | 6 | `D` |

## Como Interpretar

- `A`: referencia para demonstracao, Studio, MCP e coletas iniciais.
- `B`: util, mas ainda precisa fechar lacunas antes de virar referencia nacional.
- `C`: provider promissor, adequado para hardening e testes de contrato.
- `D`: fonte mapeada ou contextual; nao deve liderar jurimetria ampla.

Uma fonte de alto valor juridico pode ter score baixo se o acesso live, a
paginacao, os filtros ou a documentacao ainda nao estiverem maduros.
