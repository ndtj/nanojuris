# Auditoria do contrato de busca unificada

Gerado em `2026-08-20T07:45:04+00:00` a partir das declarações runtime e dos artefatos locais de smoke/discovery.

## Resposta executiva

A busca unificada compartilha o envelope de saída, mas não oferece filtros nem perfis de dados equivalentes. Há **41 providers unificados** entre **45 runtime**; **4** ficam fora por contrato/categoria.
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

Perfis: `{"precedent": 4, "decision": 34, "curated": 2, "hybrid_decision_precedent": 1}`
Paginação: `{"page": 25, "local_window": 9, "offset": 6, "none": 1}`
Texto integral: `{"not_available": 5, "link_only": 7, "detail_call": 23, "inline_summary": 1, "inline": 4, "inline_result_text": 1}`
Completude: `{"reported_total_and_page_window": 10, "reported_total_and_source_page_window": 1, "reported_html_page_only": 1, "reported_total_and_offset_window": 4, "observed_window_only": 6, "observed_window_or_source_limit": 1, "reported_window_or_source_page_limit": 5, "itemCount_and_page_window": 1, "observed_edition_window": 1, "spring_page_total_elements": 1, "CountAcordaoDocumento_or_CountDecisaoMonocratica": 1, "x_total_count_and_page_window": 1, "reported_tjpr_window": 1, "reported_form_total_and_page_window": 6, "reported_html_total_and_start_rows_window": 1}`

## Filtros

A contagem indica quantos providers declaram o filtro como nativo. Filtros ausentes sao tratados como `unsupported`; nao ha pos-filtro silencioso.

| Filtro | Providers |
|---|---:|
| `text` | 41 |
| `courts` | 1 |
| `types` | 18 |
| `all_words` | 4 |
| `any_words` | 4 |
| `without_words` | 4 |
| `exact_phrase` | 14 |
| `rapporteur` | 5 |
| `updated_from` | 19 |
| `updated_to` | 19 |
| `published_from` | 20 |
| `published_to` | 20 |
| `number` | 35 |
| `party_name` | 0 |
| `party_document` | 0 |
| `lawyer_name` | 0 |
| `oab` | 0 |
| `precatory_number` | 0 |
| `police_document` | 0 |
| `cda` | 0 |
| `source_origin` | 3 |
| `source_origins` | 2 |
| `fetch_details` | 1 |

## Matriz por provider

| Provider | Perfil | Canônicos | Filtros | Paginação | Completude | Texto | Live | Lacunas |
|---|---|---|---:|---|---|---|---|---|
| `bnp_pangea` | precedent | CanonicalPrecedent | 10/23 | page | reported_total_and_page_window | not_available | query_contract_rejected | live_status_query_contract_rejected |
| `cjf_jurisprudencia` | decision | CanonicalDecision | 3/23 | local_window | reported_total_and_source_page_window | link_only | access_controlled | live_status_access_controlled |
| `cnj_jurisprudencia` | curated | CanonicalDecision, CanonicalDocument | 4/23 | page | reported_html_page_only | link_only | valid_data | - |
| `justica_eleitoral_sjur` | precedent | ProviderCatalog | 0/23 | none | catalog_snapshot_only | not_available | não registrado | excluded_from_unified_search |
| `stf_informativo` | decision | CanonicalDecision | 2/23 | local_window | reported_total_and_page_window | not_available | source_unavailable | live_status_source_unavailable |
| `stf_juris` | decision | CanonicalDecision | 6/23 | offset | reported_total_and_offset_window | link_only | source_unavailable | live_status_source_unavailable |
| `stj_dados_abertos_jurisprudencia` | decision | CanonicalDecision, ProviderCatalog, ResearchRun | 0/23 | catalog_offset | CKAN_result_count_and_resource_metadata | unknown | query_contract_rejected | excluded_from_unified_search, full_text_access_evidence_unknown, full_text_not_declared, observed_filters_not_promoted_to_contract, live_status_query_contract_rejected |
| `stj_informativo` | decision | CanonicalDecision | 2/23 | local_window | observed_window_only | link_only | valid_data | - |
| `stj_scon` | decision | CanonicalDecision, CanonicalDocument | 2/23 | page | reported_total_and_page_window | detail_call | valid_data | - |
| `stm_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 2/23 | offset | reported_total_and_offset_window | detail_call | valid_data | - |
| `tce_sp_jurisprudencia` | precedent | CanonicalPrecedent | 2/23 | local_window | observed_window_only | link_only | valid_data | - |
| `tcu_jurisprudencia` | hybrid_decision_precedent | CanonicalDecision, CanonicalPrecedent | 2/23 | local_window | observed_window_or_source_limit | inline_summary | valid_data | - |
| `tjac_cjsg` | decision | CanonicalDecision, CanonicalDocument | 6/23 | page | reported_window_or_source_page_limit | detail_call | valid_data | - |
| `tjal_cjsg` | decision | CanonicalDecision, CanonicalDocument | 6/23 | page | reported_window_or_source_page_limit | detail_call | valid_data | - |
| `tjam_cjsg` | decision | CanonicalDecision, CanonicalDocument | 6/23 | page | reported_window_or_source_page_limit | detail_call | source_unavailable | live_status_source_unavailable |
| `tjba_graphql` | decision | CanonicalDecision, CanonicalDocument | 7/23 | page | itemCount_and_page_window | detail_call | valid_data | - |
| `tjce_cjsg` | decision | CanonicalDecision, CanonicalDocument | 6/23 | page | reported_window_or_source_page_limit | detail_call | source_unavailable | live_status_source_unavailable |
| `tjce_informativos` | curated | CanonicalDecision | 5/23 | local_window | observed_edition_window | not_available | valid_data | - |
| `tjce_sjuris` | decision | CanonicalDecision | 7/23 | page | spring_page_total_elements | inline | valid_data | - |
| `tjdf_juris` | decision | CanonicalDecision, CanonicalDocument | 10/23 | page | reported_total_and_page_window | detail_call | valid_data | - |
| `tjgo_projudi_jurisprudencia` | decision | CanonicalDecision | 2/23 | page | reported_total_and_page_window | inline_result_text | valid_data | - |
| `tjma_jurisconsult` | catalog | ProviderCatalog | 1/23 | none | public_catalog_snapshot_only | not_implemented | access_controlled | excluded_from_unified_search, live_status_access_controlled |
| `tjms_cjsg` | decision | CanonicalDecision, CanonicalDocument | 6/23 | page | reported_window_or_source_page_limit | detail_call | valid_data | - |
| `tjmt_jurisprudencia_api` | decision | CanonicalDecision | 4/23 | page | CountAcordaoDocumento_or_CountDecisaoMonocratica | inline | valid_data | - |
| `tjpa_jurisprudencia_bff` | decision | CanonicalDecision | 6/23 | page | reported_total_and_page_window | inline | valid_data | - |
| `tjpb_pje_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 6/23 | page | reported_total_and_page_window | detail_call | valid_data | - |
| `tjpe_jurisprudencia` | decision | CanonicalDecision | 5/23 | offset | x_total_count_and_page_window | inline | source_unavailable | live_status_source_unavailable |
| `tjpi_juspi` | decision | CanonicalDecision, CanonicalDocument | 7/23 | page | reported_total_and_page_window | detail_call | valid_data | - |
| `tjpr_jurisprudencia` | decision | CanonicalDecision | 6/23 | page | reported_tjpr_window | not_available | valid_data | - |
| `tjrj_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 6/23 | page | reported_form_total_and_page_window | detail_call | valid_data | - |
| `tjro_liame` | precedent | CanonicalPrecedent | 5/23 | page | reported_total_and_page_window | not_implemented | valid_data | excluded_from_unified_search |
| `tjrr_juris` | decision | CanonicalDecision, CanonicalDocument | 7/23 | page | reported_total_and_page_window | detail_call | valid_data | - |
| `tjrs_solr` | decision | CanonicalDecision | 5/23 | offset | reported_total_and_offset_window | not_available | valid_data | - |
| `tjsc_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 6/23 | page | reported_form_total_and_page_window | detail_call | valid_data | - |
| `tjsp_cjsg` | decision | CanonicalDecision, CanonicalDocument | 2/23 | page | reported_total_and_page_window | detail_call | access_controlled | live_status_access_controlled |
| `tjsp_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 6/23 | page | reported_form_total_and_page_window | detail_call | valid_data | - |
| `tjsp_nugepnac` | precedent | CanonicalPrecedent | 3/23 | local_window | observed_window_only | link_only | valid_data | - |
| `tjto_jurisprudencia` | decision | CanonicalDecision | 7/23 | offset | reported_html_total_and_start_rows_window | detail_call | valid_data | - |
| `tnu_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 6/23 | page | reported_form_total_and_page_window | detail_call | valid_data | - |
| `tre_sp_temas` | precedent | CanonicalPrecedent | 2/23 | local_window | observed_window_only | link_only | source_unavailable | live_status_source_unavailable |
| `trf2_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 6/23 | page | reported_form_total_and_page_window | detail_call | valid_data | - |
| `trf4_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 2/23 | local_window | observed_window_only | detail_call | valid_data | - |
| `trf5_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 5/23 | none | observed_window_only | detail_call | valid_data | - |
| `trf6_eproc_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 6/23 | page | reported_form_total_and_page_window | detail_call | valid_data | - |
| `tst_jurisprudencia` | decision | CanonicalDecision, CanonicalDocument | 11/23 | offset | reported_total_and_offset_window | detail_call | valid_data | - |

## Critério de maturação

Um provider só deve ser promovido como plenamente equivalente na busca unificada quando tiver perfil semântico explícito, filtros classificados como nativos/traduzidos/pós-filtro local ou não suportados, paginação e completude comprovadas, identidade estável, fixtures de estados e evidência live válida.

A matriz JSON é a fonte estruturada deste relatório: `unified-contract-matrix.json`.
