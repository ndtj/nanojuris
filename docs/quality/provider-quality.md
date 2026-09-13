# Provider quality scorecard

Gerado por o build_provider_quality.py --write; nao edite manualmente.

Este scorecard e offline e independente da saude live. Um bloqueio de rede, WAF,
CAPTCHA ou timeout permanece explicito em live_status e nunca e convertido em vazio.

- Catalogo avaliado: docs/registry/provider-catalog.full.json (3120fed4a209...).
- Providers runtime avaliados: **80** de **85** entradas.
- Providers com lacuna critica: **0**.
- Providers bloqueados ou sem live recente: **8**.
- Golden set: **8** cenarios sanitizados.

## Dimensoes

| Dimensao | Peso |
| --- | ---: |
| authority_scope | 10 |
| contract_errors | 15 |
| identity | 15 |
| textual_content | 15 |
| dates_temporality | 10 |
| provenance_trace | 15 |
| pagination_completeness | 10 |
| tests_fixtures | 5 |
| documentation_operations | 5 |

## Matriz

| Provider | Score | Tier | Criticos | Live | Evidencia |
| --- | ---: | --- | ---: | --- | --- |
| bnp_pangea | 88 | gold | 0 | valid | access_statuses, completeness_contract |
| cjf_jurisprudencia | 91 | gold | 0 | access_control_required | access_statuses, completeness_contract |
| cnj_jurisprudencia | 87 | gold | 0 | valid | access_statuses, completeness_contract |
| eproc_jurisprudencia_federal | 87 | gold | 0 | not_checked_in_latest_focused_run | access_statuses, completeness_contract |
| falcao_jt | 85 | gold | 0 | access_control_required | access_statuses, completeness_contract |
| justica_eleitoral_sjur | 59 | bronze | 0 | source_unavailable | access_statuses, completeness_contract |
| stf_informativo | 82 | silver | 0 | source_unavailable | access_statuses, completeness_contract |
| stf_juris | 88 | gold | 0 | blocked_transport | access_statuses, completeness_contract |
| stj_dados_abertos_jurisprudencia | 96 | gold | 0 | valid | access_statuses, completeness_contract |
| stj_informativo | 86 | gold | 0 | valid | access_statuses, completeness_contract |
| stj_scon | 94 | gold | 0 | access_control_required | access_statuses, completeness_contract |
| stm_jurisprudencia | 87 | gold | 0 | valid | access_statuses, completeness_contract |
| tce_pr_viajuris | 86 | gold | 0 | valid | access_statuses, completeness_contract |
| tce_sp_jurisprudencia | 87 | gold | 0 | empty_unconfirmed | access_statuses, completeness_contract |
| tcu_jurisprudencia | 86 | gold | 0 | valid | access_statuses, completeness_contract |
| tjac_banco_sentencas | 75 | silver | 0 | valid | access_statuses, completeness_contract |
| tjac_cjsg | 88 | gold | 0 | valid | access_statuses, completeness_contract |
| tjac_ementario_jurisprudencia | 89 | gold | 0 | valid | access_statuses, completeness_contract |
| tjal_cjsg | 88 | gold | 0 | valid | access_statuses, completeness_contract |
| tjal_esmal_banco_sentencas | 94 | gold | 0 | valid | access_statuses, completeness_contract |
| tjal_turma_recursal_ementario | 85 | gold | 0 | public_textual_recursal | access_statuses, completeness_contract |
| tjam_cjsg | 90 | gold | 0 | valid | access_statuses, completeness_contract |
| tjap_banco_sentencas | 90 | gold | 0 | valid | access_statuses, completeness_contract |
| tjap_tucujuris | 87 | gold | 0 | access_controlled | access_statuses, completeness_contract |
| tjba_graphql | 95 | gold | 0 | valid | access_statuses, completeness_contract |
| tjce_cjsg | 88 | gold | 0 | valid | access_statuses, completeness_contract |
| tjce_informativos | 86 | gold | 0 | valid | access_statuses, completeness_contract |
| tjce_sjuris | 85 | gold | 0 | valid | access_statuses, completeness_contract |
| tjdf_juris | 94 | gold | 0 | valid | access_statuses, completeness_contract |
| tjes_cjpg | 88 | gold | 0 | valid | access_statuses, completeness_contract |
| tjes_jurisprudencia | 88 | gold | 0 | valid | access_statuses, completeness_contract |
| tjes_turma_recursal | 88 | gold | 0 | valid | access_statuses, completeness_contract |
| tjgo_projudi_jurisprudencia | 95 | gold | 0 | valid | access_statuses, completeness_contract |
| tjma_informativos | 92 | gold | 0 | valid | access_statuses, completeness_contract |
| tjma_jurisconsult | 92 | gold | 0 | access_controlled | access_statuses, completeness_contract |
| tjmg_dspace_jurisprudencia | 91 | gold | 0 | valid | access_statuses, completeness_contract |
| tjmg_ejef_boletim_jurisprudencia | 96 | gold | 0 | valid | access_statuses, completeness_contract |
| tjmg_jurisprudencia | 91 | gold | 0 | valid | access_statuses, completeness_contract |
| tjmmg_jurisprudencia_api | 87 | gold | 0 | valid | access_statuses, completeness_contract |
| tjmrs_jurisprudencia | 81 | silver | 0 | valid | access_statuses, completeness_contract |
| tjms_cjpg | 87 | gold | 0 | valid | access_statuses, completeness_contract |
| tjms_cjsg | 88 | gold | 0 | valid | access_statuses, completeness_contract |
| tjmsp_jurisprudencia | 83 | silver | 0 | access_control_required | access_statuses, completeness_contract |
| tjmt_jurisprudencia_api | 86 | gold | 0 | valid | access_statuses, completeness_contract |
| tjpa_jurisprudencia_bff | 85 | gold | 0 | valid | access_statuses, completeness_contract |
| tjpb_pje_jurisprudencia | 89 | gold | 0 | valid | access_statuses, completeness_contract |
| tjpe_jurisprudencia | 85 | gold | 0 | valid | access_statuses, completeness_contract |
| tjpi_juspi | 93 | gold | 0 | valid | access_statuses, completeness_contract |
| tjpr_jurisprudencia | 93 | gold | 0 | valid | access_statuses, completeness_contract |
| tjrj_banco_sentencas | 88 | gold | 0 | partial | access_statuses, completeness_contract |
| tjrj_ejuris | 90 | gold | 0 | valid | access_statuses, completeness_contract |
| tjrj_eproc_jurisprudencia | 87 | gold | 0 | valid | access_statuses, completeness_contract |
| tjrn_jurisprudencia | 95 | gold | 0 | valid | access_statuses, completeness_contract |
| tjro_jurisprudencia | 88 | gold | 0 | valid | access_statuses, completeness_contract |
| tjro_liame | 88 | gold | 0 | valid | access_statuses, completeness_contract |
| tjrr_juris | 91 | gold | 0 | valid | access_statuses, completeness_contract |
| tjrs_solr | 92 | gold | 0 | valid | access_statuses, completeness_contract |
| tjsc_eproc_jurisprudencia | 87 | gold | 0 | valid | access_statuses, completeness_contract |
| tjse_boletim_jurisprudencia | 90 | gold | 0 | valid | access_statuses, completeness_contract |
| tjse_jurisprudencia | 83 | silver | 0 | blocked_access_control_no_reproducible_result | access_statuses, completeness_contract |
| tjsp_cjpg | 87 | gold | 0 | valid | access_statuses, completeness_contract |
| tjsp_cjsg | 88 | gold | 0 | valid | access_statuses, completeness_contract |
| tjsp_eproc_jurisprudencia | 87 | gold | 0 | valid | access_statuses, completeness_contract |
| tjsp_nugepnac | 89 | gold | 0 | reachable_empty_data | access_statuses, completeness_contract |
| tjto_jurisprudencia | 90 | gold | 0 | valid | access_statuses, completeness_contract |
| tnu_eproc_jurisprudencia | 87 | gold | 0 | valid | access_statuses, completeness_contract |
| tre_sjur_first_degree | 93 | gold | 0 | valid | access_statuses, completeness_contract |
| tre_sjur_jurisprudencia | 93 | gold | 0 | partial | access_statuses, completeness_contract |
| tre_sp_temas | 76 | silver | 0 | source_unavailable | access_statuses, completeness_contract |
| trf2_eproc_jurisprudencia | 87 | gold | 0 | valid | access_statuses, completeness_contract |
| trf3_jurisprudencia | 88 | gold | 0 | transport_error | access_statuses, completeness_contract |
| trf4_eproc_jurisprudencia | 87 | gold | 0 | valid | access_statuses, completeness_contract |
| trf5_jurisprudencia | 88 | gold | 0 | valid | access_statuses, completeness_contract |
| trf6_eproc_jurisprudencia | 87 | gold | 0 | valid | access_statuses, completeness_contract |
| trt15_jurisprudencia | 96 | gold | 0 | not_checked_in_latest_focused_run | access_statuses, completeness_contract |
| trt2_basis_jurisprudencia | 89 | gold | 0 | partial | access_statuses, completeness_contract |
| trt2_ementario_jurisprudencia | 91 | gold | 0 | valid | access_statuses, completeness_contract |
| trt2_pje_jurisprudencia | 85 | gold | 0 | access_control_required | access_statuses, completeness_contract |
| trt3_ementario_jurisprudencia | 77 | silver | 0 | valid | access_statuses, completeness_contract |
| trt4_sumulas_jurisprudencia | 77 | silver | 0 | valid_curated_context | access_statuses, completeness_contract |
| trt6_jurisprudencia | 91 | gold | 0 | valid | access_statuses, completeness_contract |
| trt8_pje_jurisprudencia | 91 | gold | 0 | valid | access_statuses, completeness_contract |
| trt9_nugepnac_jurisprudencia | 77 | silver | 0 | valid_curated_context | access_statuses, completeness_contract |
| tse_sjur_jurisprudencia | 94 | gold | 0 | valid | access_statuses, completeness_contract |
| tst_jurisprudencia | 89 | gold | 0 | valid | access_statuses, completeness_contract |

## Regras de promocao

- gold: score >= 85 e nenhuma lacuna critica; ainda requer aceite humano para release.
- silver: score >= 70 e nenhuma lacuna critica.
- bronze: score >= 50 e nenhuma lacuna critica.
- blocked: existe lacuna critica; nao promover para coleta automatica.
- mapped: contrato insuficiente para uma avaliacao operacional.

Saude live, licenca de reutilizacao, termos do tribunal e aprovacao de release
continuam gates independentes e nao sao inferidos por este relatorio.
