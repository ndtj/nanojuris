# Improvement Queue

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

Esta fila usa o catalogo consolidado para orientar a proxima rodada de
amadurecimento dos providers. Ela privilegia fontes de jurisprudencia textual
que ja participam da busca unificada, mas ainda possuem lacunas objetivas.

| Ordem | Fonte | Prioridade | Score | Papel | Proxima acao |
| ---: | --- | --- | ---: | --- | --- |
| 1 | `tjsp_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 68 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 2 | `tjac_cjsg` | `P0_harden_for_unified_search` | 69 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 3 | `tjal_cjsg` | `P0_harden_for_unified_search` | 69 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 4 | `tjam_cjsg` | `P0_harden_for_unified_search` | 69 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 5 | `tjms_cjsg` | `P0_harden_for_unified_search` | 69 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 6 | `stf_juris` | `P0_harden_for_unified_search` | 70 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 7 | `stm_jurisprudencia` | `P0_harden_for_unified_search` | 71 | `primary_textual_jurisprudence` | completar secoes faltantes do dossie |
| 8 | `tjrj_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 71 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 9 | `tjgo_projudi_jurisprudencia` | `P0_harden_for_unified_search` | 73 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 10 | `tjsp_cjsg` | `P0_harden_for_unified_search` | 73 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 11 | `cjf_jurisprudencia` | `P0_harden_for_unified_search` | 74 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 12 | `stj_informativo` | `P0_harden_for_unified_search` | 74 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 13 | `stj_scon` | `P0_harden_for_unified_search` | 74 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 14 | `stf_informativo` | `P0_harden_for_unified_search` | 75 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 15 | `trf4_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 77 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 16 | `tjpi_juspi` | `P0_harden_for_unified_search` | 78 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 17 | `tjsc_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 78 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 18 | `trf5_jurisprudencia` | `P0_harden_for_unified_search` | 78 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 19 | `tjrr_juris` | `P0_harden_for_unified_search` | 79 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 20 | `tjpa_jurisprudencia_bff` | `P0_harden_for_unified_search` | 80 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 21 | `tjpb_pje_jurisprudencia` | `P0_harden_for_unified_search` | 80 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 22 | `tnu_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 81 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 23 | `trf2_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 81 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 24 | `trf6_eproc_jurisprudencia` | `P0_harden_for_unified_search` | 81 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 25 | `tjpr_jurisprudencia` | `P0_harden_for_unified_search` | 82 | `primary_textual_jurisprudence` | rodar validacao live pequena com termo juridico padrao |
| 26 | `tjba_graphql` | `P0_harden_for_unified_search` | 83 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 27 | `tjrs_solr` | `P0_harden_for_unified_search` | 83 | `primary_textual_jurisprudence` | manter monitoramento e ampliar fixtures por variacao juridica |
| 28 | `tst_jurisprudencia` | `P0_harden_for_unified_search` | 87 | `primary_textual_jurisprudence` | fechar checklist objetivo do dossie |
| 29 | `tjdf_juris` | `P0_reference_provider` | 88 | `primary_textual_jurisprudence` | validar inteiro teor com hash, tamanho e access_status |
| 30 | `justica_eleitoral_sjur` | `P1_candidate_contract` | 11 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 31 | `tjce_cjsg` | `P1_candidate_contract` | 11 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 32 | `tjma_jurisconsult` | `P1_candidate_contract` | 11 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 33 | `tjmt_jurisprudencia_api` | `P1_candidate_contract` | 11 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 34 | `trf3_jurisprudencia` | `P1_candidate_contract` | 11 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 35 | `trt2_pje_jurisprudencia` | `P1_candidate_contract` | 11 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 36 | `falcao_jt` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 37 | `tjap_tucujuris` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 38 | `tjce_sjuris` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 39 | `tjes_jurisprudencia` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 40 | `tjmg_jurisprudencia` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 41 | `tjpe_jurisprudencia` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 42 | `tjrn_jurisprudencia` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 43 | `tjro_liame` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 44 | `tjse_jurisprudencia` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 45 | `tjto_jurisprudencia` | `P1_candidate_contract` | 15 | `mapped_candidate` | reproduzir contrato HTTP publico e criar fixture minima |
| 46 | `stj_dados_abertos_jurisprudencia` | `P1_contextual_value` | 47 | `dataset_pipeline` | fechar checklist objetivo do dossie |
| 47 | `tre_sp_temas` | `P1_contextual_value` | 56 | `curated_context` | fechar checklist objetivo do dossie |
| 48 | `tjsp_nugepnac` | `P1_contextual_value` | 60 | `precedent_context` | fechar checklist objetivo do dossie |
| 49 | `cnj_jurisprudencia` | `P1_contextual_value` | 69 | `curated_context` | fechar checklist objetivo do dossie |
| 50 | `bnp_pangea` | `P1_contextual_value` | 73 | `precedent_context` | completar secoes faltantes do dossie |
| 51 | `tjce_informativos` | `P1_contextual_value` | 77 | `curated_context` | fechar checklist objetivo do dossie |
| 52 | `eproc_jurisprudencia_federal` | `P1_family_reuse` | 17 | `implementation_family` | reproduzir contrato HTTP publico e criar fixture minima |

## Regra De Execucao

Para subir um provider na fila, feche primeiro o item mais objetivo: fixture,
erro classificado, paginacao, campo canonico ou documentacao faltante. Depois
regenere o catalogo e deixe o score mostrar a evolucao.
