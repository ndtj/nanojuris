# Improvement Queue

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

Esta fila usa o catalogo consolidado para orientar a proxima rodada de
amadurecimento dos providers. Ela privilegia fontes de jurisprudencia textual
que ja participam da busca unificada, mas ainda possuem lacunas objetivas.

| Ordem | Fonte | Prioridade | Score | Papel | Proxima acao |
| ---: | --- | --- | ---: | --- | --- |
| 1 | `tjro_jurisprudencia` | `P0_harden_for_unified_search` | 82 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 2 | `tjal_esmal_banco_sentencas` | `P0_harden_for_unified_search` | 84 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 3 | `tjmg_ejef_boletim_jurisprudencia` | `P0_harden_for_unified_search` | 84 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 4 | `tjes_jurisprudencia` | `P0_harden_for_unified_search` | 87 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 5 | `tjes_turma_recursal` | `P0_harden_for_unified_search` | 87 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 6 | `tjmg_dspace_jurisprudencia` | `P0_harden_for_unified_search` | 87 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 7 | `tjmg_jurisprudencia` | `P0_harden_for_unified_search` | 87 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 8 | `tjms_cjpg` | `P0_harden_for_unified_search` | 87 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 9 | `tjsp_cjpg` | `P0_harden_for_unified_search` | 87 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 10 | `stm_jurisprudencia` | `P0_harden_for_unified_search` | 88 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 11 | `tjac_cjsg` | `P0_harden_for_unified_search` | 88 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 12 | `tjac_ementario_jurisprudencia` | `P0_harden_for_unified_search` | 88 | `primary_textual_jurisprudence` | manter monitoramento e ampliar fixtures por variacao juridica |
| 13 | `tjes_cjpg` | `P0_harden_for_unified_search` | 88 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 14 | `tjsp_cjsg` | `P0_harden_for_unified_search` | 88 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 15 | `tjal_cjsg` | `P0_harden_for_unified_search` | 89 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 16 | `tjam_cjsg` | `P0_harden_for_unified_search` | 89 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 17 | `tjce_cjsg` | `P0_harden_for_unified_search` | 89 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 18 | `tjce_sjuris` | `P0_harden_for_unified_search` | 89 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 19 | `tjgo_projudi_jurisprudencia` | `P0_harden_for_unified_search` | 89 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 20 | `tjms_cjsg` | `P0_harden_for_unified_search` | 89 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 21 | `tjrn_jurisprudencia` | `P0_harden_for_unified_search` | 89 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 22 | `tjse_boletim_jurisprudencia` | `P0_harden_for_unified_search` | 89 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 23 | `trf5_jurisprudencia` | `P0_harden_for_unified_search` | 89 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 24 | `tjsp_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 90 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 25 | `tjap_banco_sentencas` | `P0_harden_for_unified_search` | 91 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 26 | `tjmt_jurisprudencia_api` | `P0_harden_for_unified_search` | 91 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 27 | `tjpe_jurisprudencia` | `P0_harden_for_unified_search` | 91 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 28 | `tjrj_ejuris` | `P0_harden_for_unified_search` | 91 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 29 | `tjrj_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 91 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 30 | `tjsc_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 91 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 31 | `tjto_jurisprudencia` | `P0_harden_for_unified_search` | 91 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 32 | `trt8_pje_jurisprudencia` | `P0_harden_for_unified_search` | 91 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 33 | `trt2_ementario_jurisprudencia` | `P0_harden_for_unified_search` | 93 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 34 | `stj_informativo` | `P0_reference_provider` | 90 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 35 | `tjrr_juris` | `P0_reference_provider` | 92 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 36 | `tjrs_solr` | `P0_reference_provider` | 92 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 37 | `trf4_eproc_jurisprudencia` | `P0_reference_provider` | 92 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 38 | `tjpi_juspi` | `P0_reference_provider` | 93 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 39 | `tjpr_jurisprudencia` | `P0_reference_provider` | 93 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 40 | `tjba_graphql` | `P0_reference_provider` | 94 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 41 | `tjdf_juris` | `P0_reference_provider` | 94 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 42 | `trf2_eproc_jurisprudencia` | `P0_reference_provider` | 94 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 43 | `trf6_eproc_jurisprudencia` | `P0_reference_provider` | 94 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 44 | `tst_jurisprudencia` | `P0_reference_provider` | 94 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 45 | `tjpa_jurisprudencia_bff` | `P0_reference_provider` | 95 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 46 | `tjpb_pje_jurisprudencia` | `P0_reference_provider` | 95 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 47 | `tnu_eproc_jurisprudencia` | `P0_reference_provider` | 95 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 48 | `stf_informativo` | `P1_access_diagnostics` | 73 | `specialized_context` | fechar checklist objetivo do dossie |
| 49 | `justica_eleitoral_sjur` | `P1_contextual_value` | 44 | `curated_context` | fechar checklist objetivo do dossie |
| 50 | `tre_sp_temas` | `P1_contextual_value` | 58 | `curated_context` | fechar checklist objetivo do dossie |
| 51 | `trt4_sumulas_jurisprudencia` | `P1_contextual_value` | 59 | `curated_context` | completar secoes faltantes do dossie |
| 52 | `trt9_nugepnac_jurisprudencia` | `P1_contextual_value` | 59 | `curated_context` | completar secoes faltantes do dossie |
| 53 | `trt3_ementario_jurisprudencia` | `P1_contextual_value` | 61 | `curated_context` | completar secoes faltantes do dossie |
| 54 | `tre_sjur_jurisprudencia` | `P1_contextual_value` | 65 | `curated_context` | completar secoes faltantes do dossie |
| 55 | `trt2_basis_jurisprudencia` | `P1_contextual_value` | 66 | `curated_context` | completar secoes faltantes do dossie |
| 56 | `tjma_informativos` | `P1_contextual_value` | 68 | `curated_context` | validar inteiro teor com hash, tamanho e access_status |
| 57 | `tjce_informativos` | `P1_contextual_value` | 70 | `curated_context` | fechar checklist objetivo do dossie |
| 58 | `tre_sjur_first_degree` | `P1_contextual_value` | 70 | `curated_context` | fechar checklist objetivo do dossie |
| 59 | `tjsp_nugepnac` | `P1_contextual_value` | 73 | `precedent_context` | manter monitoramento e ampliar fixtures por variacao juridica |
| 60 | `stj_dados_abertos_jurisprudencia` | `P1_contextual_value` | 74 | `dataset_pipeline` | validar inteiro teor com hash, tamanho e access_status |
| 61 | `tse_sjur_jurisprudencia` | `P1_contextual_value` | 78 | `curated_context` | validar inteiro teor com hash, tamanho e access_status |
| 62 | `cnj_jurisprudencia` | `P1_contextual_value` | 83 | `curated_context` | validar inteiro teor com hash, tamanho e access_status |
| 63 | `tjro_liame` | `P1_contextual_value` | 85 | `precedent_context` | manter monitoramento e ampliar fixtures por variacao juridica |
| 64 | `bnp_pangea` | `P1_contextual_value` | 87 | `precedent_context` | manter monitoramento e ampliar fixtures por variacao juridica |

## Regra De Execucao

Para subir um provider na fila, feche primeiro o item mais objetivo: fixture,
erro classificado, paginacao, campo canonico ou documentacao faltante. Depois
regenere o catalogo e deixe o score mostrar a evolucao.
