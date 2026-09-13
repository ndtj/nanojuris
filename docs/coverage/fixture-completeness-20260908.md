# Fixture completeness gate

Gerado offline por `tools/build_fixture_completeness.py`.

- Providers runtime: **80**
- Completos no envelope de cenários: **80**
- Incompletos: **0**
- Com fixture específica versionada: **80**
- Com segunda página aplicável: **52**

A matriz combina fixture específica de cada provider com o envelope canônico compartilhado. O envelope não é resposta de tribunal: ele valida distinção de estados no transporte e na federação.

| Provider | Paginação | Fixture específica | Segunda página aplicável | Evidência | Estado |
|---|---|---:|---:|---|---|
| `bnp_pangea` | `page` | true | true | `source_plus_shared_contract` | complete |
| `cjf_jurisprudencia` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `cnj_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `eproc_jurisprudencia_federal` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `justica_eleitoral_sjur` | `none` | true | false | `source_plus_shared_contract` | complete |
| `stf_informativo` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `stf_juris` | `offset` | true | true | `source_plus_shared_contract` | complete |
| `stj_dados_abertos_jurisprudencia` | `catalog_offset` | true | true | `source_plus_shared_contract` | complete |
| `stj_informativo` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `stj_scon` | `page` | true | true | `source_plus_shared_contract` | complete |
| `stm_jurisprudencia` | `offset` | true | true | `source_plus_shared_contract` | complete |
| `tce_pr_viajuris` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `tce_sp_jurisprudencia` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `tcu_jurisprudencia` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `tjac_banco_sentencas` | `local_html_window` | true | false | `source_plus_shared_contract` | complete |
| `tjac_cjsg` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjac_ementario_jurisprudencia` | `local_pdf_window` | true | false | `source_plus_shared_contract` | complete |
| `tjal_cjsg` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjal_esmal_banco_sentencas` | `remote_page` | true | false | `source_plus_shared_contract` | complete |
| `tjal_turma_recursal_ementario` | `local_pdf_window` | true | false | `source_plus_shared_contract` | complete |
| `tjam_cjsg` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjap_banco_sentencas` | `livewire_page` | true | true | `source_plus_shared_contract` | complete |
| `tjba_graphql` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjce_cjsg` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjce_informativos` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `tjce_sjuris` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjdf_juris` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjes_cjpg` | `offset` | true | true | `source_plus_shared_contract` | complete |
| `tjes_jurisprudencia` | `offset` | true | true | `source_plus_shared_contract` | complete |
| `tjes_turma_recursal` | `offset` | true | true | `source_plus_shared_contract` | complete |
| `tjgo_projudi_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjma_informativos` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `tjma_jurisconsult` | `offset` | true | true | `source_plus_shared_contract` | complete |
| `tjmg_dspace_jurisprudencia` | `merged_collection_page` | true | true | `source_plus_shared_contract` | complete |
| `tjmg_ejef_boletim_jurisprudencia` | `offset` | true | true | `source_plus_shared_contract` | complete |
| `tjmg_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjmmg_jurisprudencia_api` | `none` | true | false | `source_plus_shared_contract` | complete |
| `tjmrs_jurisprudencia` | `none` | true | false | `source_plus_shared_contract` | complete |
| `tjms_cjpg` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjms_cjsg` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjmt_jurisprudencia_api` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjpa_jurisprudencia_bff` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjpb_pje_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjpe_jurisprudencia` | `offset` | true | true | `source_plus_shared_contract` | complete |
| `tjpi_juspi` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjpr_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjrj_banco_sentencas` | `local_pdf_window` | true | false | `source_plus_shared_contract` | complete |
| `tjrj_ejuris` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjrj_eproc_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjrn_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjro_jurisprudencia` | `offset` | true | true | `source_plus_shared_contract` | complete |
| `tjro_liame` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjrr_juris` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjrs_solr` | `offset` | true | true | `source_plus_shared_contract` | complete |
| `tjsc_eproc_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjse_boletim_jurisprudencia` | `edition_section` | true | true | `source_plus_shared_contract` | complete |
| `tjsp_cjpg` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjsp_cjsg` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjsp_eproc_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tjsp_nugepnac` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `tjto_jurisprudencia` | `offset` | true | true | `source_plus_shared_contract` | complete |
| `tnu_eproc_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `tre_sjur_first_degree` | `none` | true | false | `source_plus_shared_contract` | complete |
| `tre_sjur_jurisprudencia` | `none` | true | false | `source_plus_shared_contract` | complete |
| `tre_sp_temas` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `trf2_eproc_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `trf3_jurisprudencia` | `detail_links` | true | true | `source_plus_shared_contract` | complete |
| `trf4_eproc_jurisprudencia` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `trf5_jurisprudencia` | `none` | true | false | `source_plus_shared_contract` | complete |
| `trf6_eproc_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `trt15_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `trt2_basis_jurisprudencia` | `dspace_page` | true | true | `source_plus_shared_contract` | complete |
| `trt2_ementario_jurisprudencia` | `local_window` | true | false | `source_plus_shared_contract` | complete |
| `trt3_ementario_jurisprudencia` | `remote_volume_search_local_pdf_window` | true | false | `source_plus_shared_contract` | complete |
| `trt4_sumulas_jurisprudencia` | `local_html_window` | true | false | `source_plus_shared_contract` | complete |
| `trt6_jurisprudencia` | `offset` | true | true | `source_plus_shared_contract` | complete |
| `trt8_pje_jurisprudencia` | `page` | true | true | `source_plus_shared_contract` | complete |
| `trt9_nugepnac_jurisprudencia` | `local_pdf_window` | true | false | `source_plus_shared_contract` | complete |
| `tse_sjur_jurisprudencia` | `none` | true | false | `source_plus_shared_contract` | complete |
| `tst_jurisprudencia` | `offset` | true | true | `source_plus_shared_contract` | complete |

Nenhum corpo de fonte foi obtido pela geração deste artefato.
