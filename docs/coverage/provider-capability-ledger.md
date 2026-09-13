# Provider capability ledger

Generated offline from current catalog, contracts, document inventory, quality and Juscraper evidence.

Operational policy: cache TTL 600.0s; telemetry 30d; minimum interval 2.0s; bounded pages 3; curated sources opt-in; owner NanoJuris maintainer; scope core_and_conditional.

## Summary

- providers: 85
- runtime: 80
- candidates: 5
- families: 0
- by_lifecycle: {'implemented': 80, 'candidate': 5}
- by_live_status: {'valid': 62, 'access_control_required': 5, 'not_checked_in_latest_focused_run': 2, 'source_unavailable': 3, 'blocked_transport': 1, 'empty_unconfirmed': 1, 'public_textual_recursal': 1, 'access_controlled': 2, 'partial': 3, 'blocked_access_control_no_reproducible_result': 1, 'reachable_empty_data': 1, 'transport_error': 1, 'valid_curated_context': 2}
- by_wave: {'B-specialized': 3, 'C-context': 30, 'D-candidate': 5, 'A-primary': 47}
- providers_with_gaps: 85
- native_filter_declarations: 199
- unverified_filter_declarations: 0
- terminal_filter_declarations: 2695
- full_text_declared: 83

## Provider gaps

| Provider | Runtime | Live | Filters (native/unsupported/unverified) | Full text | Gaps |
|---|---:|---|---:|---|---:|
| `bnp_pangea` | True | valid | 10/25/0 | not_available | 3 |
| `cjf_jurisprudencia` | True | access_control_required | 0/27/0 | detail_call | 6 |
| `cnj_jurisprudencia` | True | valid | 0/24/0 | document_link | 1 |
| `eproc_jurisprudencia_federal` | True | not_checked_in_latest_focused_run | 8/20/0 | detail_call | 5 |
| `falcao_jt` | False | access_control_required | 0/0/0 | unknown | 5 |
| `justica_eleitoral_sjur` | True | source_unavailable | 0/32/0 | not_available | 4 |
| `stf_informativo` | True | source_unavailable | 2/30/0 | not_available | 5 |
| `stf_juris` | True | blocked_transport | 1/23/0 | link_only | 6 |
| `stj_dados_abertos_jurisprudencia` | True | valid | 0/32/0 | detail_call | 1 |
| `stj_informativo` | True | valid | 2/30/0 | document_link | 1 |
| `stj_scon` | True | access_control_required | 2/29/0 | detail_call | 5 |
| `stm_jurisprudencia` | True | valid | 2/30/0 | detail_call | 3 |
| `tce_pr_viajuris` | True | valid | 0/24/0 | document_link | 1 |
| `tce_sp_jurisprudencia` | True | empty_unconfirmed | 0/28/0 | document_link | 3 |
| `tcu_jurisprudencia` | True | valid | 0/26/0 | inline_summary | 1 |
| `tjac_banco_sentencas` | True | valid | 0/0/0 | document_link | 3 |
| `tjac_cjsg` | True | valid | 1/18/0 | detail_call | 3 |
| `tjac_ementario_jurisprudencia` | True | valid | 0/26/0 | summary_only | 1 |
| `tjal_cjsg` | True | valid | 1/18/0 | detail_call | 3 |
| `tjal_esmal_banco_sentencas` | True | valid | 4/26/0 | document_link | 2 |
| `tjal_turma_recursal_ementario` | True | public_textual_recursal | 0/26/0 | summary_only | 3 |
| `tjam_cjsg` | True | valid | 1/18/0 | detail_call | 3 |
| `tjap_banco_sentencas` | True | valid | 2/27/0 | inline | 3 |
| `tjap_tucujuris` | False | access_controlled | 0/0/0 | access_blocked | 4 |
| `tjba_graphql` | True | valid | 1/19/0 | detail_call | 2 |
| `tjce_cjsg` | True | valid | 1/18/0 | detail_call | 3 |
| `tjce_informativos` | True | valid | 0/23/0 | not_available | 2 |
| `tjce_sjuris` | True | valid | 0/22/0 | inline | 2 |
| `tjdf_juris` | True | valid | 1/12/0 | detail_call | 2 |
| `tjes_cjpg` | True | valid | 3/23/0 | inline | 3 |
| `tjes_jurisprudencia` | True | valid | 1/26/0 | inline | 2 |
| `tjes_turma_recursal` | True | valid | 1/26/0 | inline | 2 |
| `tjgo_projudi_jurisprudencia` | True | valid | 3/21/0 | inline_result_text | 3 |
| `tjma_informativos` | True | valid | 0/29/0 | document_link | 1 |
| `tjma_jurisconsult` | True | access_controlled | 8/23/0 | access_blocked | 3 |
| `tjmg_dspace_jurisprudencia` | True | valid | 3/25/0 | document_link | 3 |
| `tjmg_ejef_boletim_jurisprudencia` | True | valid | 3/27/0 | document_link | 3 |
| `tjmg_jurisprudencia` | True | valid | 9/22/0 | detail_call | 3 |
| `tjmmg_jurisprudencia_api` | True | valid | 8/25/0 | inline | 2 |
| `tjmrs_jurisprudencia` | True | valid | 1/27/0 | inline | 5 |
| `tjms_cjpg` | True | valid | 1/24/0 | inline | 3 |
| `tjms_cjsg` | True | valid | 1/18/0 | detail_call | 3 |
| `tjmsp_jurisprudencia` | False | access_control_required | 0/0/0 | unknown | 10 |
| `tjmt_jurisprudencia_api` | True | valid | 1/20/0 | inline | 2 |
| `tjpa_jurisprudencia_bff` | True | valid | 0/20/0 | inline | 2 |
| `tjpb_pje_jurisprudencia` | True | valid | 2/13/0 | detail_call | 2 |
| `tjpe_jurisprudencia` | True | valid | 0/21/0 | inline | 3 |
| `tjpi_juspi` | True | valid | 4/24/0 | detail_call | 2 |
| `tjpr_jurisprudencia` | True | valid | 6/15/0 | document_link | 2 |
| `tjrj_banco_sentencas` | True | partial | 0/27/0 | document_link | 4 |
| `tjrj_ejuris` | True | valid | 1/19/0 | inline_result_text | 2 |
| `tjrj_eproc_jurisprudencia` | True | valid | 6/22/0 | detail_call | 3 |
| `tjrn_jurisprudencia` | True | valid | 2/20/0 | inline | 2 |
| `tjro_jurisprudencia` | True | valid | 5/9/0 | detail_call | 3 |
| `tjro_liame` | True | valid | 1/30/0 | not_offered_by_source | 1 |
| `tjrr_juris` | True | valid | 7/22/0 | detail_call | 2 |
| `tjrs_solr` | True | valid | 1/24/0 | detail_call | 2 |
| `tjsc_eproc_jurisprudencia` | True | valid | 6/22/0 | detail_call | 3 |
| `tjse_boletim_jurisprudencia` | True | valid | 5/24/0 | inline | 3 |
| `tjse_jurisprudencia` | False | blocked_access_control_no_reproducible_result | 0/0/0 | access_blocked | 4 |
| `tjsp_cjpg` | True | valid | 1/24/0 | inline | 3 |
| `tjsp_cjsg` | True | valid | 1/23/0 | detail_call | 3 |
| `tjsp_eproc_jurisprudencia` | True | valid | 6/22/0 | detail_call | 3 |
| `tjsp_nugepnac` | True | reachable_empty_data | 3/28/0 | link_only | 3 |
| `tjto_jurisprudencia` | True | valid | 1/22/0 | detail_call | 2 |
| `tnu_eproc_jurisprudencia` | True | valid | 6/22/0 | detail_call | 2 |
| `tre_sjur_first_degree` | True | valid | 0/0/0 | inline | 4 |
| `tre_sjur_jurisprudencia` | True | partial | 1/29/0 | inline | 9 |
| `tre_sp_temas` | True | source_unavailable | 0/29/0 | document_link | 4 |
| `trf2_eproc_jurisprudencia` | True | valid | 6/22/0 | detail_call | 2 |
| `trf3_jurisprudencia` | True | transport_error | 2/27/0 | detail_call | 5 |
| `trf4_eproc_jurisprudencia` | True | valid | 7/20/0 | detail_call | 2 |
| `trf5_jurisprudencia` | True | valid | 1/25/0 | detail_call | 3 |
| `trf6_eproc_jurisprudencia` | True | valid | 6/22/0 | detail_call | 2 |
| `trt15_jurisprudencia` | True | not_checked_in_latest_focused_run | 8/21/0 | detail_call | 4 |
| `trt2_basis_jurisprudencia` | True | partial | 3/26/0 | document_link | 10 |
| `trt2_ementario_jurisprudencia` | True | valid | 0/26/0 | document_link | 1 |
| `trt2_pje_jurisprudencia` | False | access_control_required | 0/0/0 | access_blocked | 5 |
| `trt3_ementario_jurisprudencia` | True | valid | 0/27/0 | document_link | 8 |
| `trt4_sumulas_jurisprudencia` | True | valid_curated_context | 0/26/0 | document_link | 10 |
| `trt6_jurisprudencia` | True | valid | 0/0/0 | inline_result_text | 3 |
| `trt8_pje_jurisprudencia` | True | valid | 7/19/0 | detail_call | 3 |
| `trt9_nugepnac_jurisprudencia` | True | valid_curated_context | 1/27/0 | document_link | 10 |
| `tse_sjur_jurisprudencia` | True | valid | 0/29/0 | inline | 2 |
| `tst_jurisprudencia` | True | valid | 11/20/0 | detail_call | 3 |

Unknown and blocked states are preserved; this artifact does not promote providers or claim national coverage.
