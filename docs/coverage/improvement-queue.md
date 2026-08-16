# Improvement Queue

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

Esta fila usa o catalogo consolidado para orientar a proxima rodada de
amadurecimento dos providers. Ela privilegia fontes de jurisprudencia textual
que ja participam da busca unificada, mas ainda possuem lacunas objetivas.

| Ordem | Fonte | Prioridade | Score | Papel | Proxima acao |
| ---: | --- | --- | ---: | --- | --- |
| 1 | `cjf_jurisprudencia` | `P0_harden_for_unified_search` | 73 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 2 | `stf_juris` | `P0_harden_for_unified_search` | 73 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 3 | `stm_jurisprudencia` | `P0_harden_for_unified_search` | 74 | `primary_textual_jurisprudence` | completar secoes faltantes do dossie |
| 4 | `tjce_cjsg` | `P0_harden_for_unified_search` | 75 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 5 | `tjgo_projudi_jurisprudencia` | `P0_harden_for_unified_search` | 75 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 6 | `tjsp_cjsg` | `P0_harden_for_unified_search` | 75 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 7 | `tjsp_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 76 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 8 | `stf_informativo` | `P0_harden_for_unified_search` | 78 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 9 | `stj_scon` | `P0_harden_for_unified_search` | 78 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 10 | `tjam_cjsg` | `P0_harden_for_unified_search` | 78 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 11 | `tjac_cjsg` | `P0_harden_for_unified_search` | 80 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 12 | `tjal_cjsg` | `P0_harden_for_unified_search` | 80 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 13 | `tjms_cjsg` | `P0_harden_for_unified_search` | 80 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 14 | `trf4_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 80 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 15 | `trf5_jurisprudencia` | `P0_harden_for_unified_search` | 80 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 16 | `stj_informativo` | `P0_harden_for_unified_search` | 81 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 17 | `tjrj_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 82 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 18 | `tjpi_juspi` | `P0_harden_for_unified_search` | 83 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 19 | `tjpe_jurisprudencia` | `P0_harden_for_unified_search` | 84 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 20 | `tjrr_juris` | `P0_harden_for_unified_search` | 84 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 21 | `tjmt_jurisprudencia_api` | `P0_harden_for_unified_search` | 86 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 22 | `tjto_jurisprudencia` | `P0_harden_for_unified_search` | 86 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 23 | `tjce_sjuris` | `P0_harden_for_unified_search` | 87 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 24 | `tjpa_jurisprudencia_bff` | `P0_harden_for_unified_search` | 87 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 25 | `tjpb_pje_jurisprudencia` | `P0_harden_for_unified_search` | 87 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 26 | `tjsc_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 89 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 27 | `trf2_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 89 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 28 | `trf6_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 89 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 29 | `tjba_graphql` | `P0_harden_for_unified_search` | 90 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 30 | `tnu_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 90 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 31 | `tst_jurisprudencia` | `P0_harden_for_unified_search` | 90 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 32 | `tjpr_jurisprudencia` | `P0_reference_provider` | 89 | `primary_textual_jurisprudence` | manter monitoramento e ampliar fixtures por variacao juridica |
| 33 | `tjrs_solr` | `P0_reference_provider` | 89 | `primary_textual_jurisprudence` | manter monitoramento e ampliar fixtures por variacao juridica |
| 34 | `tjdf_juris` | `P0_reference_provider` | 94 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 35 | `justica_eleitoral_sjur` | `P1_candidate_contract` | 11 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 36 | `trf3_jurisprudencia` | `P1_candidate_contract` | 11 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 37 | `trt2_pje_jurisprudencia` | `P1_candidate_contract` | 11 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 38 | `falcao_jt` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 39 | `tjap_tucujuris` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 40 | `tjes_jurisprudencia` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 41 | `tjmg_jurisprudencia` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 42 | `tjrn_jurisprudencia` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 43 | `tjse_jurisprudencia` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 44 | `stj_dados_abertos_jurisprudencia` | `P1_contextual_value` | 47 | `dataset_pipeline` | fechar checklist objetivo do dossie |
| 45 | `tre_sp_temas` | `P1_contextual_value` | 56 | `curated_context` | fechar checklist objetivo do dossie |
| 46 | `tjsp_nugepnac` | `P1_contextual_value` | 60 | `precedent_context` | fechar checklist objetivo do dossie |
| 47 | `cnj_jurisprudencia` | `P1_contextual_value` | 69 | `curated_context` | fechar checklist objetivo do dossie |
| 48 | `bnp_pangea` | `P1_contextual_value` | 73 | `precedent_context` | completar secoes faltantes do dossie |
| 49 | `tjro_liame` | `P1_contextual_value` | 74 | `precedent_context` | manter monitoramento e ampliar fixtures por variacao juridica |
| 50 | `tjce_informativos` | `P1_contextual_value` | 77 | `curated_context` | fechar checklist objetivo do dossie |
| 51 | `eproc_jurisprudencia_federal` | `P1_family_reuse` | 17 | `implementation_family` | reproduzir contrato HTTP publico e criar fixture minima |

## Regra De Execucao

Para subir um provider na fila, feche primeiro o item mais objetivo: fixture,
erro classificado, paginacao, campo canonico ou documentacao faltante. Depois
regenere o catalogo e deixe o score mostrar a evolucao.
