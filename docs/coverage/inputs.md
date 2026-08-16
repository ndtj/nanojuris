# Inputs

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

Esta matriz mostra as entradas declaradas por fonte. Ela e util para humanos
planejarem coletas e para IAs escolherem providers sem inventar filtros.

| Fonte | Texto | Filtros | Paginacao | Catalogo | Sugestoes |
| --- | ---: | --- | --- | ---: | ---: |
| `bnp_pangea` | sim | text, number, courts, types, all_words, any_words, without_words, exact_phrase, updated_from, updated_to | `unknown` | sim | sim |
| `cjf_jurisprudencia` | sim | text, number, types | `unknown` | nao | nao |
| `cnj_jurisprudencia` | sim | text, number, published_from, published_to, page | `page` | sim | nao |
| `eproc_jurisprudencia_federal` | nao | - | `unknown` | nao | nao |
| `falcao_jt` | nao | - | `unknown` | nao | nao |
| `justica_eleitoral_sjur` | nao | - | `unknown` | nao | nao |
| `stf_informativo` | sim | text, number | `unknown` | sim | nao |
| `stf_juris` | sim | text, number, published_from, published_to, updated_from, updated_to | `unknown` | nao | nao |
| `stj_dados_abertos_jurisprudencia` | nao | catalog_query, rows, dataset_id, resource_id, format, max_bytes, force | `catalog_offset` | sim | nao |
| `stj_informativo` | sim | text, number | `local_window` | nao | nao |
| `stj_scon` | sim | text, number | `unknown` | nao | nao |
| `stm_jurisprudencia` | sim | text, number | `offset` | nao | nao |
| `tce_sp_jurisprudencia` | sim | text, types | `unknown` | sim | nao |
| `tcu_jurisprudencia` | sim | text, number | `unknown` | sim | nao |
| `tjac_cjsg` | sim | text, number, exact_phrase, updated_from, updated_to, types, order_by | `page` | nao | nao |
| `tjal_cjsg` | sim | text, number, exact_phrase, updated_from, updated_to, types, order_by | `page` | nao | nao |
| `tjam_cjsg` | sim | text, number, exact_phrase, updated_from, updated_to, types, order_by | `page` | nao | nao |
| `tjap_tucujuris` | nao | - | `unknown` | nao | nao |
| `tjba_graphql` | sim | text, exact_phrase, number, updated_from, updated_to, published_from, published_to, order_by | `page` | sim | nao |
| `tjce_cjsg` | sim | text, number, exact_phrase, updated_from, updated_to, types, order_by | `page` | nao | nao |
| `tjce_informativos` | sim | text, number, types, published_from, published_to, page | `local_window` | sim | nao |
| `tjce_sjuris` | sim | text, all_words, any_words, without_words, exact_phrase, types, source_origins | `page` | nao | nao |
| `tjdf_juris` | sim | text, exact_phrase, all_words, any_words, without_words, rapporteur, published_from, published_to, updated_from, updated_to | `page` | nao | nao |
| `tjes_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `tjgo_projudi_jurisprudencia` | sim | text, number | `page` | nao | nao |
| `tjma_jurisconsult` | nao | types, catalog | `none` | sim | nao |
| `tjmg_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `tjms_cjsg` | sim | text, number, exact_phrase, updated_from, updated_to, types, order_by | `page` | nao | nao |
| `tjmt_jurisprudencia_api` | sim | text, published_from, published_to, types, order_by | `page` | nao | nao |
| `tjpa_jurisprudencia_bff` | sim | text, types, source_origins, published_from, published_to, case_class, subject, rapporteur | `page` | sim | nao |
| `tjpb_pje_jurisprudencia` | sim | text, number, case_class, judging_body, rapporteur, published_from, published_to, source_origin | `page` | sim | nao |
| `tjpe_jurisprudencia` | sim | text, number, published_from, published_to, types, order_by | `offset` | nao | nao |
| `tjpi_juspi` | sim | text, number | `page` | nao | nao |
| `tjpr_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to | `page` | nao | nao |
| `tjrj_eproc_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to | `page` | nao | nao |
| `tjrn_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `tjro_liame` | sim | text, number, published_from, published_to, types, page | `page` | sim | nao |
| `tjrr_juris` | sim | text, number, exact_phrase, updated_from, updated_to, published_from, published_to | `page` | nao | nao |
| `tjrs_solr` | sim | text, exact_phrase, number, page, published_from, published_to | `offset` | nao | nao |
| `tjsc_eproc_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to | `page` | nao | nao |
| `tjse_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `tjsp_cjsg` | sim | text, number | `unknown` | nao | nao |
| `tjsp_eproc_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to | `unknown` | nao | nao |
| `tjsp_nugepnac` | sim | text, number, types | `unknown` | sim | nao |
| `tjto_jurisprudencia` | sim | text, exact_phrase, number, rapporteur, source_origin, types, order_by, page, fetch_details | `offset` | nao | nao |
| `tnu_eproc_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to | `page` | nao | nao |
| `tre_sp_temas` | sim | text, exact_phrase | `unknown` | sim | nao |
| `trf2_eproc_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to | `page` | nao | nao |
| `trf3_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `trf4_eproc_jurisprudencia` | sim | text, number | `unknown` | nao | nao |
| `trf5_jurisprudencia` | sim | text, number, published_from, published_to, types | `unknown` | nao | nao |
| `trf6_eproc_jurisprudencia` | sim | text, number, published_from, published_to, updated_from, updated_to | `page` | nao | nao |
| `trt2_pje_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `tst_jurisprudencia` | sim | text, all_words, any_words, without_words, exact_phrase, number, published_from, published_to, updated_from, updated_to, types | `offset` | sim | nao |
