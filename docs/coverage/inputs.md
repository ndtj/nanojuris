# Inputs

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

Esta matriz mostra as entradas declaradas por fonte. Ela e util para humanos
planejarem coletas e para IAs escolherem providers sem inventar filtros.

| Fonte | Texto | Filtros | Paginacao | Catalogo | Sugestoes |
| --- | ---: | --- | --- | ---: | ---: |
| `bnp_pangea` | sim | text, number, courts, types, all_words, any_words, without_words, exact_phrase, updated_from, updated_to | `page` | sim | sim |
| `cjf_jurisprudencia` | sim | text, number, types | `local_window` | nao | nao |
| `cnj_jurisprudencia` | sim | text, number, published_from, published_to, page | `page` | sim | nao |
| `eproc_jurisprudencia_federal` | sim | text, number, authority | `local_window` | nao | nao |
| `falcao_jt` | sim | - | `unknown_until_contract` | sim | nao |
| `justica_eleitoral_sjur` | nao | - | `none` | sim | nao |
| `stf_informativo` | sim | text, number | `local_window` | sim | nao |
| `stf_juris` | sim | text, number, all_words, any_words, without_words, published_from, published_to, updated_from, updated_to, order_by | `offset` | nao | nao |
| `stj_dados_abertos_jurisprudencia` | nao | catalog_query, rows, dataset_id, resource_id, metadata_resource_id, text_resource_id, format, max_bytes, force | `catalog_offset` | sim | nao |
| `stj_informativo` | sim | text, number | `local_window` | nao | nao |
| `stj_scon` | sim | text, number | `page` | nao | nao |
| `stm_jurisprudencia` | sim | text, number | `offset` | nao | nao |
| `tce_pr_viajuris` | sim | text, number, published_from, published_to | `local_window` | sim | nao |
| `tce_sp_jurisprudencia` | sim | text, types | `local_window` | sim | nao |
| `tcu_jurisprudencia` | sim | text, number, collection, published_from, published_to | `local_window` | sim | nao |
| `tjac_banco_sentencas` | sim | text, exact_phrase, number, degree, instance, branch, authority, collection, page | `local_html_window` | nao | nao |
| `tjac_cjsg` | sim | text, number, exact_phrase, case_class, judging_body, updated_from, updated_to, published_from, published_to, types, order_by | `page` | nao | nao |
| `tjac_ementario_jurisprudencia` | sim | text, exact_phrase, number, without_words, degree, instance, branch, authority, collection, page | `local_pdf_window` | nao | nao |
| `tjal_cjsg` | sim | text, number, exact_phrase, case_class, judging_body, updated_from, updated_to, published_from, published_to, types, order_by | `page` | nao | nao |
| `tjal_esmal_banco_sentencas` | sim | text, exact_phrase, number, legal_area, degree, instance, branch, authority, collection, page | `remote_page` | nao | nao |
| `tjal_turma_recursal_ementario` | sim | text, exact_phrase, number, without_words, degree, instance, branch, authority, collection, page | `local_pdf_window` | nao | nao |
| `tjam_cjsg` | sim | text, number, exact_phrase, case_class, judging_body, updated_from, updated_to, published_from, published_to, types, order_by | `page` | nao | nao |
| `tjap_banco_sentencas` | sim | text, exact_phrase, number, case_class, judging_body, types, judgment_date_from, judgment_date_to, page | `livewire_page` | nao | nao |
| `tjap_tucujuris` | sim | text, number, case_class, rapporteur, judging_body, degree, instance, branch, collection, judgment_date_from, judgment_date_to, source_origin, decision_type, types | `offset` | sim | nao |
| `tjba_graphql` | sim | text, exact_phrase, all_words, any_words, without_words, number, updated_from, updated_to, published_from, published_to, order_by | `page` | sim | nao |
| `tjce_cjsg` | sim | text, number, exact_phrase, case_class, judging_body, updated_from, updated_to, published_from, published_to, types, order_by | `page` | nao | nao |
| `tjce_informativos` | sim | text, number, types, published_from, published_to, page | `local_window` | sim | nao |
| `tjce_sjuris` | sim | text, all_words, any_words, without_words, exact_phrase, types, source_origins | `page` | nao | nao |
| `tjdf_juris` | sim | text, exact_phrase, all_words, any_words, without_words, number, rapporteur, source_origin, source_origins, case_class, judging_body, published_from, published_to, updated_from, updated_to, judgment_date_from, judgment_date_to, fetch_details | `page` | nao | nao |
| `tjes_cjpg` | sim | text, exact_phrase, number, rapporteur, updated_from, updated_to, order_by | `offset` | nao | nao |
| `tjes_jurisprudencia` | sim | text, exact_phrase, number, page | `offset` | nao | nao |
| `tjes_turma_recursal` | sim | text, exact_phrase, number, page | `offset` | nao | nao |
| `tjgo_projudi_jurisprudencia` | sim | text, exact_phrase, number, types, updated_from, updated_to, published_from, published_to, degree, instance, source_origin, decision_type, collection, document_type, branch, authority | `page` | nao | nao |
| `tjma_informativos` | nao | page, authority, branch, degree, instance, collection | `local_window` | sim | nao |
| `tjma_jurisconsult` | nao | types, catalog, text, exact_phrase, case_class, judging_body, rapporteur, published_from, published_to, page | `offset` | sim | nao |
| `tjmg_dspace_jurisprudencia` | sim | text, exact_phrase, number, degree, instance, branch, page | `merged_collection_page` | nao | nao |
| `tjmg_ejef_boletim_jurisprudencia` | sim | text, exact_phrase, number, degree, instance, branch, authority, collection, page | `offset` | nao | nao |
| `tjmg_jurisprudencia` | sim | text, number, types, case_class, rapporteur, judging_body, courts, legal_area, document_type, decision_type, exact_phrase, all_words, degree, instance, branch, collection, judgment_date_from, judgment_date_to, published_from, published_to, order_by | `page` | nao | nao |
| `tjmmg_jurisprudencia_api` | sim | text, exact_phrase, number, case_class, rapporteur, judgment_date_from, judgment_date_to, published_from, published_to, document_type | `none` | nao | nao |
| `tjmrs_jurisprudencia` | nao | number, fetch_details, degree, instance, branch, collection, document_type, decision_type | `none` | nao | nao |
| `tjms_cjpg` | sim | text, exact_phrase, number, updated_from, updated_to | `page` | nao | nao |
| `tjms_cjsg` | sim | text, number, exact_phrase, case_class, judging_body, updated_from, updated_to, published_from, published_to, types, order_by | `page` | nao | nao |
| `tjmsp_jurisprudencia` | sim | - | `unknown_until_contract` | nao | nao |
| `tjmt_jurisprudencia_api` | sim | text, exact_phrase, all_words, any_words, without_words, number, published_from, published_to, types, order_by | `page` | nao | nao |
| `tjpa_jurisprudencia_bff` | sim | text, types, source_origins, published_from, published_to, fetch_details | `page` | sim | nao |
| `tjpb_pje_jurisprudencia` | sim | text, number, case_class, judging_body, rapporteur, published_from, published_to, judgment_date_from, judgment_date_to, source_origin, degree, instance | `page` | sim | nao |
| `tjpe_jurisprudencia` | sim | text, number, rapporteur, case_class, published_from, published_to, judgment_date_from, judgment_date_to, types, order_by | `offset` | nao | nao |
| `tjpi_juspi` | sim | text, exact_phrase, number, types, rapporteur, source_origin, updated_from, updated_to, degree, instance, decision_type | `page` | nao | nao |
| `tjpr_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to, judgment_date_from, judgment_date_to, courts, rapporteur, case_class, judging_body, types, fetch_details | `page` | nao | nao |
| `tjrj_banco_sentencas` | sim | text, exact_phrase, number, degree, instance, branch, authority, collection, page | `local_pdf_window` | nao | nao |
| `tjrj_ejuris` | sim | text, exact_phrase, number, types, document_type, decision_type, published_from, published_to, updated_from, updated_to, degree, instance, branch, authority, collection, source_origin | `page` | nao | nao |
| `tjrj_eproc_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to, source_origin, degree, instance | `page` | nao | nao |
| `tjrn_jurisprudencia` | sim | text, exact_phrase, number, page, degree, instance, case_class, judging_body, source_origin, decision_type, judgment_date_from, judgment_date_to | `page` | nao | nao |
| `tjro_jurisprudencia` | sim | text, exact_phrase, number, rapporteur, updated_from, updated_to, fetch_details | `offset` | nao | nao |
| `tjro_liame` | sim | text, number, published_from, published_to, types, page | `page` | sim | nao |
| `tjrr_juris` | sim | text, number, exact_phrase, rapporteur, judging_body, judgment_date_from, judgment_date_to, degree, instance, branch, authority, collection | `page` | nao | nao |
| `tjrs_solr` | sim | text, exact_phrase, number, page, published_from, published_to | `offset` | nao | nao |
| `tjsc_eproc_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to, source_origin, degree, instance | `page` | nao | nao |
| `tjse_boletim_jurisprudencia` | sim | text, exact_phrase, number, degree, instance, branch, page, judgment_date_from, judgment_date_to | `edition_section` | nao | nao |
| `tjse_jurisprudencia` | sim | text, number, case_class, rapporteur, judging_body, degree, instance, document_type, judgment_date_from, judgment_date_to | `unknown_until_challenge_passed` | sim | nao |
| `tjsp_cjpg` | sim | text, exact_phrase, number, updated_from, updated_to | `page` | nao | nao |
| `tjsp_cjsg` | sim | text, exact_phrase, number, types, updated_from, updated_to, order_by | `page` | nao | nao |
| `tjsp_eproc_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to, source_origin, degree, instance | `page` | nao | nao |
| `tjsp_nugepnac` | sim | text, number, types | `local_window` | sim | nao |
| `tjto_jurisprudencia` | sim | text, exact_phrase, number, rapporteur, source_origin, degree, instance, types, order_by, page, fetch_details | `offset` | nao | nao |
| `tnu_eproc_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to, source_origin, degree, instance | `page` | nao | nao |
| `tre_sjur_first_degree` | sim | text, exact_phrase, number, all_words, any_words, without_words, authority, branch, degree, instance, collection, types, document_type, decision_type, case_class, rapporteur, party_name, judgment_date_from, judgment_date_to, published_from, published_to, election_year, observations, tags, municipality, publication_source, publication_number, publication_volume, uf | `none` | nao | nao |
| `tre_sjur_jurisprudencia` | sim | text, exact_phrase, number, all_words, any_words, without_words, authority, branch, degree, instance, collection, types, document_type, decision_type, case_class, rapporteur, party_name, judgment_date_from, judgment_date_to, published_from, published_to, election_year, observations, tags, municipality, publication_source, publication_number, publication_volume, uf | `none` | nao | nao |
| `tre_sp_temas` | sim | text, exact_phrase | `local_window` | sim | nao |
| `trf2_eproc_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to, source_origin, degree, instance | `page` | nao | nao |
| `trf3_jurisprudencia` | nao | number, fetch_details, degree, instance, branch, collection, document_type, decision_type | `detail_links` | nao | nao |
| `trf4_eproc_jurisprudencia` | sim | text, number | `local_window` | nao | nao |
| `trf5_jurisprudencia` | sim | text, number, published_from, published_to, types | `none` | nao | nao |
| `trf6_eproc_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to, source_origin, degree, instance | `page` | nao | nao |
| `trt15_jurisprudencia` | sim | text, all_words, any_words, exact_phrase, without_words, case_class, judging_body, rapporteur, published_from, published_to, page, document_type | `page` | sim | nao |
| `trt2_basis_jurisprudencia` | sim | text, exact_phrase, number, degree, instance, branch, authority, collection, document_type, page | `dspace_page` | nao | nao |
| `trt2_ementario_jurisprudencia` | sim | text, exact_phrase, number, degree, instance, branch, authority, collection, document_type, page | `local_window` | sim | nao |
| `trt2_pje_jurisprudencia` | sim | text, number, all_words, any_words, without_words, exact_phrase, case_class, judging_body, rapporteur, published_from, published_to, degree, instance, document_type, decision_type, types | `offset_unverified` | nao | nao |
| `trt3_ementario_jurisprudencia` | sim | text, exact_phrase, number, page | `remote_volume_search_local_pdf_window` | nao | nao |
| `trt4_sumulas_jurisprudencia` | sim | text, exact_phrase, number, document_type, page | `local_html_window` | nao | nao |
| `trt6_jurisprudencia` | sim | text, number, published_from, published_to, rapporteur, judging_body, authority, branch, degree, instance, collection, document_type | `offset` | nao | nao |
| `trt8_pje_jurisprudencia` | sim | text, all_words, any_words, without_words, case_class, judging_body, rapporteur, published_from, published_to, document_type, degree, instance, branch, authority, collection, page, fetch_details | `page` | nao | nao |
| `trt9_nugepnac_jurisprudencia` | sim | text, exact_phrase, number, collection, page | `local_pdf_window` | nao | nao |
| `tse_sjur_jurisprudencia` | sim | text, exact_phrase, number, all_words, any_words, without_words, authority, branch, degree, instance, collection | `none` | nao | nao |
| `tst_jurisprudencia` | sim | text, all_words, any_words, without_words, exact_phrase, number, published_from, published_to, updated_from, updated_to, types | `offset` | sim | nao |
