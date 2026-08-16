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
| `tjdf_juris` | 88 | 14 | 25 | 18 | 16 | 15 | `A` |
| `tst_jurisprudencia` | 87 | 19 | 25 | 16 | 12 | 15 | `A` |
| `tjba_graphql` | 83 | 19 | 25 | 12 | 12 | 15 | `B` |
| `tjrs_solr` | 83 | 16 | 22 | 14 | 16 | 15 | `B` |
| `tjpr_jurisprudencia` | 82 | 16 | 22 | 12 | 17 | 15 | `B` |
| `tnu_eproc_jurisprudencia` | 81 | 10 | 25 | 16 | 15 | 15 | `B` |
| `trf2_eproc_jurisprudencia` | 81 | 10 | 25 | 16 | 15 | 15 | `B` |
| `trf6_eproc_jurisprudencia` | 81 | 10 | 25 | 16 | 15 | 15 | `B` |
| `tjpa_jurisprudencia_bff` | 80 | 19 | 25 | 12 | 9 | 15 | `B` |
| `tjpb_pje_jurisprudencia` | 80 | 19 | 25 | 12 | 9 | 15 | `B` |
| `tjrr_juris` | 79 | 16 | 25 | 12 | 11 | 15 | `B` |
| `tjpi_juspi` | 78 | 14 | 25 | 12 | 12 | 15 | `B` |
| `tjsc_eproc_jurisprudencia` | 78 | 10 | 25 | 12 | 16 | 15 | `B` |
| `trf5_jurisprudencia` | 78 | 11 | 25 | 12 | 15 | 15 | `B` |
| `tjce_informativos` | 77 | 18 | 22 | 12 | 10 | 15 | `B` |
| `trf4_eproc_jurisprudencia` | 77 | 10 | 25 | 18 | 9 | 15 | `B` |
| `stf_informativo` | 75 | 12 | 22 | 16 | 10 | 15 | `B` |
| `cjf_jurisprudencia` | 74 | 10 | 22 | 12 | 15 | 15 | `B` |
| `stj_informativo` | 74 | 14 | 22 | 12 | 11 | 15 | `B` |
| `stj_scon` | 74 | 10 | 25 | 8 | 16 | 15 | `B` |
| `bnp_pangea` | 73 | 16 | 22 | 12 | 8 | 15 | `B` |
| `tjgo_projudi_jurisprudencia` | 73 | 14 | 22 | 10 | 12 | 15 | `B` |
| `tjsp_cjsg` | 73 | 10 | 25 | 8 | 15 | 15 | `B` |
| `stm_jurisprudencia` | 71 | 14 | 25 | 12 | 5 | 15 | `B` |
| `tjrj_eproc_jurisprudencia` | 71 | 10 | 25 | 12 | 9 | 15 | `B` |
| `stf_juris` | 70 | 12 | 22 | 8 | 13 | 15 | `B` |
| `cnj_jurisprudencia` | 69 | 17 | 18 | 12 | 10 | 12 | `C` |
| `tjac_cjsg` | 69 | 10 | 25 | 10 | 9 | 15 | `C` |
| `tjal_cjsg` | 69 | 10 | 25 | 10 | 9 | 15 | `C` |
| `tjam_cjsg` | 69 | 10 | 25 | 10 | 9 | 15 | `C` |
| `tjms_cjsg` | 69 | 10 | 25 | 10 | 9 | 15 | `C` |
| `tjsp_eproc_jurisprudencia` | 68 | 10 | 22 | 12 | 9 | 15 | `C` |
| `tcu_jurisprudencia` | 65 | 12 | 14 | 14 | 13 | 12 | `C` |
| `tjsp_nugepnac` | 60 | 12 | 15 | 12 | 9 | 12 | `C` |
| `tre_sp_temas` | 56 | 12 | 11 | 12 | 9 | 12 | `C` |
| `tce_sp_jurisprudencia` | 49 | 12 | 6 | 10 | 9 | 12 | `D` |
| `stj_dados_abertos_jurisprudencia` | 47 | 10 | 9 | 12 | 12 | 4 | `D` |
| `eproc_jurisprudencia_federal` | 17 | 0 | 0 | 2 | 15 | 0 | `D` |
| `falcao_jt` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjap_tucujuris` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjce_sjuris` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjes_jurisprudencia` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjmg_jurisprudencia` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjpe_jurisprudencia` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjrn_jurisprudencia` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjro_liame` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjse_jurisprudencia` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `tjto_jurisprudencia` | 15 | 0 | 0 | 2 | 13 | 0 | `D` |
| `justica_eleitoral_sjur` | 11 | 0 | 0 | 2 | 9 | 0 | `D` |
| `tjce_cjsg` | 11 | 0 | 0 | 2 | 9 | 0 | `D` |
| `tjma_jurisconsult` | 11 | 0 | 0 | 2 | 9 | 0 | `D` |
| `tjmt_jurisprudencia_api` | 11 | 0 | 0 | 2 | 9 | 0 | `D` |
| `trf3_jurisprudencia` | 11 | 0 | 0 | 2 | 9 | 0 | `D` |
| `trt2_pje_jurisprudencia` | 11 | 0 | 0 | 2 | 9 | 0 | `D` |

## Como Interpretar

- `A`: referencia para demonstracao, Studio, MCP e coletas iniciais.
- `B`: util, mas ainda precisa fechar lacunas antes de virar referencia nacional.
- `C`: provider promissor, adequado para hardening e testes de contrato.
- `D`: fonte mapeada ou contextual; nao deve liderar jurimetria ampla.

Uma fonte de alto valor juridico pode ter score baixo se o acesso live, a
paginacao, os filtros ou a documentacao ainda nao estiverem maduros.
