# Auditoria do contrato de busca unificada

Gerado em `2026-09-11T05:49:40+00:00` a partir das declarações runtime e dos artefatos locais de smoke/discovery.

## Resposta executiva

A busca unificada compartilha o envelope de saída, mas não oferece filtros nem perfis de dados equivalentes. Há **52 providers unificados** entre **77 runtime**; **25** ficam fora por contrato/categoria.
Na fotografia live registrada, **33/44** providers entregaram dados válidos (**75.0%**).
O discovery aprofundado observou **3169 rotas** e **299 campos de filtro**, com **11** sinais de controle de acesso.

## Lacunas principais

- `pagination_contract_unknown`: a fonte não comprova como a janela remota termina.
- `completeness_contract_unknown`: total, truncamento ou exaustividade não estão formalizados.
- `full_text_access_evidence_unknown`: texto integral é anunciado ou possível, mas a forma de obtenção não está comprovada.
- `observed_filters_not_promoted_to_contract`: a fonte expos um filtro que ainda nao foi promovido com semantica runtime.
- `decision_and_precedent_profiles_need_discriminator`: a fonte entrega decisão e precedente e exige discriminação semântica.
- estados live de acesso/indisponibilidade/query inválida ainda reduzem a cobertura operacional.

## Distribuição do contrato

Perfis: `{"precedent": 2, "curated": 1, "decision": 48, "hybrid_decision_precedent": 1}`
Paginação: `{"page": 31, "local_window": 5, "offset": 10, "local_pdf_window": 1, "remote_page": 1, "livewire_page": 1, "merged_collection_page": 1, "edition_section": 1, "none": 1}`
Texto integral: `{"not_available": 1, "document_link": 8, "detail_call": 26, "inline_summary": 1, "summary_only": 1, "inline": 12, "inline_result_text": 2, "not_offered_by_source": 1}`
Completude: `{"reported_total_and_page_window": 15, "reported_html_page_only": 1, "observed_window_only": 3, "reported_total_and_offset_window": 3, "complete_local_snapshot_window": 1, "observed_window_or_source_limit": 1, "reported_window_or_source_page_limit": 5, "static_volume_total_unknown": 1, "curated_html_index_total_unknown": 1, "source_window_with_approximate_total": 1, "itemCount_and_page_window": 1, "spring_page_total_elements": 1, "sum_of_three_public_collection_totals": 1, "reported_collection_total_and_offset_window": 1, "totalRecords_authoritative_public_api_capped_at_1000": 1, "CountAcordaoDocumento_or_CountDecisaoMonocratica": 1, "x_total_count_and_page_window": 1, "reported_tjpr_window": 1, "reported_form_total_and_page_window": 6, "hits_total_and_page_window": 1, "hits.total.value with offset window": 1, "section_rows_total_unknown_across_editions": 1, "reported_html_total_and_start_rows_window": 1, "bounded_topic_window_total_unknown": 1, "reported_hits_and_page_window": 1}`

## Filtros

A contagem indica quantos providers declaram o filtro como nativo. Filtros ausentes permanecem `unverified`; somente uma declaracao explicita os torna `unsupported`.

| Filtro | Providers |
|---|---:|
| `text` | 52 |
| `courts` | 47 |
| `types` | 49 |
| `all_words` | 51 |
| `any_words` | 51 |
| `without_words` | 51 |
| `exact_phrase` | 51 |
| `rapporteur` | 50 |
| `updated_from` | 50 |
| `updated_to` | 50 |
| `published_from` | 50 |
| `published_to` | 50 |
| `number` | 51 |
| `party_name` | 46 |
| `party_document` | 48 |
| `lawyer_name` | 48 |
| `oab` | 48 |
| `precatory_number` | 48 |
| `police_document` | 48 |
| `cda` | 48 |
| `source_origin` | 49 |
| `source_origins` | 49 |
| `fetch_details` | 50 |
| `case_class` | 50 |
| `judging_body` | 50 |
| `degree` | 51 |
| `instance` | 51 |
| `branch` | 51 |
| `legal_area` | 48 |
| `authority` | 51 |
| `collection` | 51 |
| `document_type` | 50 |
| `decision_type` | 49 |
| `judgment_date_from` | 49 |
| `judgment_date_to` | 49 |

## Matriz por provider

| Provider | Perfil | Canônicos | Filtros | Paginação | Completude | Texto | Live | Lacunas |
|---|---|---|---:|---|---|---|---|---|
| `bnp_pangea` | precedent | CanonicalPrecedent | 10/35 | page | reported_total_and_page_window | not_available | query_contract_rejected | live_status_query_contract_rejected |
| `cjf_jurisprudencia` | document | CanonicalDocument, DecisionBundle, JurisprudenceResult | 35/35 | local_window | reported_total_and_source_page_window | detail_call | access_controlled | excluded_from_unified_search, live_status_access_controlled |
| `cnj_jurisprudencia` | curated | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_html_page_only | document_link | valid_data | - |
| `eproc_jurisprudencia_federal` | decision | CanonicalDecision, CanonicalDocument | 35/35 | local_window | observed_window_only | detail_call | não registrado | excluded_from_unified_search |
| `justica_eleitoral_sjur` | precedent | ProviderCatalog | 35/35 | none | catalog_snapshot_only | not_available | não registrado | excluded_from_unified_search |
| `stf_informativo` | decision | CanonicalDecision | 35/35 | local_window | reported_total_and_page_window | not_available | source_unavailable | excluded_from_unified_search, live_status_source_unavailable |
| `stf_juris` | decision | CanonicalDecision | 35/35 | offset | reported_total_and_offset_window | link_only | source_unavailable | excluded_from_unified_search, live_status_source_unavailable |
| `stj_dados_abertos_jurisprudencia` | decision | CanonicalDecision, ProviderCatalog, ResearchRun | 35/35 | catalog_offset | CKAN_result_count_and_resource_metadata | detail_call | query_contract_rejected | excluded_from_unified_search, live_status_query_contract_rejected |
| `stj_informativo` | decision | CanonicalDecision, CanonicalDocument | 35/35 | local_window | observed_window_only | document_link | valid_data | - |
| `stj_scon` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_total_and_page_window | detail_call | valid_data | excluded_from_unified_search |
| `stm_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | offset | reported_total_and_offset_window | detail_call | valid_data | - |
| `tce_pr_viajuris` | decision | CanonicalDecision, CanonicalDocument | 35/35 | local_window | complete_local_snapshot_window | document_link | não registrado | - |
| `tce_sp_jurisprudencia` | precedent | CanonicalDocument, CanonicalPrecedent | 35/35 | local_window | observed_window_only | document_link | valid_data | excluded_from_unified_search |
| `tcu_jurisprudencia` | hybrid_decision_precedent | CanonicalDecision, CanonicalPrecedent | 35/35 | local_window | observed_window_or_source_limit | inline_summary | valid_data | - |
| `tjac_cjsg` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_window_or_source_page_limit | detail_call | valid_data | - |
| `tjac_ementario_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | local_pdf_window | static_volume_total_unknown | summary_only | não registrado | - |
| `tjal_cjsg` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_window_or_source_page_limit | detail_call | valid_data | - |
| `tjal_esmal_banco_sentencas` | decision | CanonicalDecision, CanonicalDocument | 35/35 | remote_page | curated_html_index_total_unknown | document_link | não registrado | - |
| `tjal_turma_recursal_ementario` | decision | CanonicalDecision, CanonicalDocument | 35/35 | local_pdf_window | static_volume_total_unknown | summary_only | não registrado | excluded_from_unified_search |
| `tjam_cjsg` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_window_or_source_page_limit | detail_call | source_unavailable | live_status_source_unavailable |
| `tjap_banco_sentencas` | decision | CanonicalDecision, CanonicalDocument | 35/35 | livewire_page | source_window_with_approximate_total | inline | não registrado | - |
| `tjba_graphql` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | itemCount_and_page_window | detail_call | valid_data | - |
| `tjce_cjsg` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_window_or_source_page_limit | detail_call | source_unavailable | live_status_source_unavailable |
| `tjce_informativos` | curated | CanonicalDecision | 35/35 | local_window | observed_edition_window | not_available | valid_data | excluded_from_unified_search |
| `tjce_sjuris` | decision | CanonicalDecision | 35/35 | page | spring_page_total_elements | inline | valid_data | - |
| `tjdf_juris` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_total_and_page_window | detail_call | valid_data | - |
| `tjes_cjpg` | decision | CanonicalDecision | 35/35 | offset | reported_total_and_page_window | inline | não registrado | - |
| `tjes_jurisprudencia` | decision | CanonicalDecision | 35/35 | offset | reported_total_and_page_window | inline | não registrado | - |
| `tjes_turma_recursal` | decision | CanonicalDecision | 35/35 | offset | reported_total_and_page_window | inline | não registrado | - |
| `tjgo_projudi_jurisprudencia` | decision | CanonicalDecision | 35/35 | page | reported_total_and_page_window | inline_result_text | valid_data | - |
| `tjma_informativos` | curated | CanonicalDecision, CanonicalDocument | 35/35 | local_window | observed_public_edition_window | document_link | não registrado | excluded_from_unified_search |
| `tjma_jurisconsult` | catalog | JurisprudenceResult, ProviderCatalog, SearchPage | 35/35 | offset | authorized_processos_int_count | access_blocked | access_controlled | excluded_from_unified_search, live_status_access_controlled |
| `tjmg_dspace_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 33/35 | merged_collection_page | sum_of_three_public_collection_totals | document_link | não registrado | - |
| `tjmg_ejef_boletim_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 8/35 | offset | reported_collection_total_and_offset_window | document_link | não registrado | - |
| `tjmg_jurisprudencia` | decision | CanonicalDecision | 35/35 | page | totalRecords_authoritative_public_api_capped_at_1000 | detail_call | não registrado | - |
| `tjmmg_jurisprudencia_api` | decision | CanonicalDecision, CanonicalDocument | 10/35 | none | complete_collection_for_exact_or_closed_date_query | inline | não registrado | excluded_from_unified_search |
| `tjmrs_jurisprudencia` | document | CanonicalDocument, JurisprudenceResult | 8/35 | none | one_public_document_for_exact_process | inline | não registrado | excluded_from_unified_search |
| `tjms_cjpg` | decision | CanonicalDecision | 35/35 | page | reported_total_and_page_window | inline | não registrado | - |
| `tjms_cjsg` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_window_or_source_page_limit | detail_call | valid_data | - |
| `tjmt_jurisprudencia_api` | decision | CanonicalDecision | 35/35 | page | CountAcordaoDocumento_or_CountDecisaoMonocratica | inline | valid_data | - |
| `tjpa_jurisprudencia_bff` | decision | CanonicalDecision | 35/35 | page | reported_total_and_page_window | inline | valid_data | - |
| `tjpb_pje_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_total_and_page_window | detail_call | valid_data | - |
| `tjpe_jurisprudencia` | decision | CanonicalDecision | 35/35 | offset | x_total_count_and_page_window | inline | source_unavailable | live_status_source_unavailable |
| `tjpi_juspi` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_total_and_page_window | detail_call | valid_data | - |
| `tjpr_jurisprudencia` | decision | CanonicalDecision | 35/35 | page | reported_tjpr_window | document_link | valid_data | - |
| `tjrj_banco_sentencas` | decision | CanonicalDecision, CanonicalDocument | 35/35 | local_pdf_window | curated_pdf_index_total_unknown | document_link | não registrado | excluded_from_unified_search |
| `tjrj_ejuris` | decision | CanonicalDecision | 35/35 | page | reported_total_and_page_window | inline_result_text | não registrado | - |
| `tjrj_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_form_total_and_page_window | detail_call | valid_data | - |
| `tjrn_jurisprudencia` | decision | CanonicalDecision | 35/35 | page | hits_total_and_page_window | inline | não registrado | - |
| `tjro_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 26/35 | offset | hits.total.value with offset window | detail_call | não registrado | - |
| `tjro_liame` | precedent | CanonicalPrecedent | 35/35 | page | reported_total_and_page_window | not_offered_by_source | valid_data | - |
| `tjrr_juris` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_total_and_page_window | detail_call | valid_data | - |
| `tjrs_solr` | decision | CanonicalDecision, CanonicalDocument | 35/35 | offset | reported_total_and_offset_window | detail_call | valid_data | - |
| `tjsc_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_form_total_and_page_window | detail_call | valid_data | - |
| `tjse_boletim_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 32/35 | edition_section | section_rows_total_unknown_across_editions | inline | não registrado | - |
| `tjsp_cjpg` | decision | CanonicalDecision | 35/35 | page | reported_total_and_page_window | inline | não registrado | - |
| `tjsp_cjsg` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_total_and_page_window | detail_call | access_controlled | live_status_access_controlled |
| `tjsp_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_form_total_and_page_window | detail_call | valid_data | - |
| `tjsp_nugepnac` | precedent | CanonicalPrecedent | 35/35 | local_window | observed_window_only | link_only | valid_data | excluded_from_unified_search |
| `tjto_jurisprudencia` | decision | CanonicalDecision | 35/35 | offset | reported_html_total_and_start_rows_window | detail_call | valid_data | - |
| `tnu_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_form_total_and_page_window | detail_call | valid_data | - |
| `tre_sjur_jurisprudencia` | precedent | JurisprudenceResult | 35/35 | none | reported_total_but_remote_window_unverified | inline | não registrado | excluded_from_unified_search |
| `tre_sp_temas` | precedent | CanonicalPrecedent | 35/35 | local_window | observed_window_only | document_link | source_unavailable | excluded_from_unified_search, live_status_source_unavailable |
| `trf2_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_form_total_and_page_window | detail_call | valid_data | - |
| `trf3_jurisprudencia` | document | CanonicalDocument, JurisprudenceResult | 35/35 | detail_links | all_documents_for_exact_process | detail_call | não registrado | excluded_from_unified_search |
| `trf4_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | local_window | observed_window_only | detail_call | valid_data | - |
| `trf5_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | none | observed_window_only | detail_call | valid_data | - |
| `trf6_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | page | reported_form_total_and_page_window | detail_call | valid_data | - |
| `trt15_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 29/35 | page | resultadosEncontrados_when_search_is_authorized | detail_call | não registrado | excluded_from_unified_search |
| `trt2_basis_jurisprudencia` | curated | CanonicalDecision, CanonicalDocument | 9/35 | dspace_page | dspace_total_unknown_curated_scope | document_link | não registrado | excluded_from_unified_search |
| `trt2_ementario_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | local_window | bounded_topic_window_total_unknown | document_link | não registrado | - |
| `trt3_ementario_jurisprudencia` | curated | CanonicalDecision, CanonicalDocument | 35/35 | remote_volume_search_local_pdf_window | static_volume_total_known_not_corpus_complete | document_link | não registrado | excluded_from_unified_search |
| `trt4_sumulas_jurisprudencia` | curated | CanonicalDecision, CanonicalDocument | 35/35 | local_html_window | static_curated_html_total_known_not_corpus_complete | document_link | não registrado | excluded_from_unified_search |
| `trt8_pje_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 16/35 | page | reported_hits_and_page_window | detail_call | não registrado | - |
| `trt9_nugepnac_jurisprudencia` | curated | CanonicalDecision, CanonicalDocument | 35/35 | local_pdf_window | static_curated_pdf_total_known_not_corpus_complete | document_link | não registrado | excluded_from_unified_search |
| `tse_sjur_jurisprudencia` | precedent | JurisprudenceResult | 35/35 | none | reported_total_but_remote_window_unverified | inline | não registrado | excluded_from_unified_search |
| `tst_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 35/35 | offset | reported_total_and_offset_window | detail_call | valid_data | - |

## Critério de maturação

Um provider só deve ser promovido como plenamente equivalente na busca unificada quando tiver perfil semântico explícito, filtros classificados como nativos/traduzidos/pós-filtro local ou não suportados, paginação e completude comprovadas, identidade estável, fixtures de estados e evidência live válida.

A matriz JSON é a fonte estruturada deste relatório: `unified-contract-matrix.json`.
