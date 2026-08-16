# Inputs

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

Esta matriz mostra as entradas declaradas por fonte. Ela e util para humanos
planejarem coletas e para IAs escolherem providers sem inventar filtros.

| Fonte | Texto | Filtros | Paginacao | Catalogo | Sugestoes |
| --- | ---: | --- | --- | ---: | ---: |
| `bnp_pangea` | sim | text, number, courts, types, all_words, any_words, without_words, exact_phrase, updated_from, updated_to | `unknown` | sim | sim |
| `cjf_jurisprudencia` | nao | text, number, types | `unknown` | nao | nao |
| `cnj_jurisprudencia` | sim | text, number, published_from, published_to, page | `page` | sim | nao |
| `eproc_jurisprudencia_federal` | nao | - | `unknown` | nao | nao |
| `falcao_jt` | nao | - | `unknown` | nao | nao |
| `justica_eleitoral_sjur` | nao | - | `unknown` | nao | nao |
| `stf_informativo` | sim | text, number | `unknown` | sim | nao |
| `stf_juris` | sim | text, number, published_from, published_to, updated_from, updated_to | `unknown` | nao | nao |
| `stj_dados_abertos_jurisprudencia` | nao | catalog_query, rows, dataset_id, resource_id, format, max_bytes, force | `catalog_offset` | sim | nao |
| `stj_informativo` | sim | text, number | `local_window` | nao | nao |
| `stj_scon` | sim | text, number | `unknown` | nao | nao |
| `stm_jurisprudencia` | nao | text, number | `offset` | nao | nao |
| `tce_sp_jurisprudencia` | sim | text, types | `unknown` | sim | nao |
| `tcu_jurisprudencia` | nao | text, number | `unknown` | sim | nao |
| `tjac_cjsg` | nao | text, number | `unknown` | nao | nao |
| `tjal_cjsg` | nao | text, number | `unknown` | nao | nao |
| `tjam_cjsg` | nao | text, number | `unknown` | nao | nao |
| `tjap_tucujuris` | nao | - | `unknown` | nao | nao |
| `tjba_graphql` | nao | text, exact_phrase, number, updated_from, updated_to, published_from, published_to, order_by | `page` | sim | nao |
| `tjce_cjsg` | nao | - | `unknown` | nao | nao |
| `tjce_informativos` | sim | text, number, types, published_from, published_to, page | `local_window` | sim | nao |
| `tjce_sjuris` | nao | - | `unknown` | nao | nao |
| `tjdf_juris` | sim | text, exact_phrase | `page` | nao | nao |
| `tjes_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `tjgo_projudi_jurisprudencia` | nao | text, number | `page` | nao | nao |
| `tjma_jurisconsult` | nao | - | `unknown` | nao | nao |
| `tjmg_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `tjms_cjsg` | nao | text, number | `unknown` | nao | nao |
| `tjmt_jurisprudencia_api` | nao | - | `unknown` | nao | nao |
| `tjpa_jurisprudencia_bff` | nao | text, types, source_origins, published_from, published_to, case_class, subject, rapporteur | `page` | sim | nao |
| `tjpb_pje_jurisprudencia` | nao | text, number, case_class, judging_body, rapporteur, published_from, published_to, source_origin | `page` | sim | nao |
| `tjpe_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `tjpi_juspi` | nao | text, number | `page` | nao | nao |
| `tjpr_jurisprudencia` | nao | text, number, published_from, published_to, updated_from, updated_to | `page` | nao | nao |
| `tjrj_eproc_jurisprudencia` | nao | text, number | `unknown` | nao | nao |
| `tjrn_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `tjro_liame` | nao | - | `unknown` | nao | nao |
| `tjrr_juris` | nao | text, number, exact_phrase, updated_from, updated_to, published_from, published_to | `page` | nao | nao |
| `tjrs_solr` | nao | text, exact_phrase, number, page, published_from, published_to | `offset` | nao | nao |
| `tjsc_eproc_jurisprudencia` | nao | text, number | `unknown` | nao | nao |
| `tjse_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `tjsp_cjsg` | nao | text, number | `unknown` | nao | nao |
| `tjsp_eproc_jurisprudencia` | nao | text, number | `unknown` | nao | nao |
| `tjsp_nugepnac` | sim | text, number, types | `unknown` | sim | nao |
| `tjto_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `tnu_eproc_jurisprudencia` | nao | text, number | `unknown` | nao | nao |
| `tre_sp_temas` | sim | text, exact_phrase | `unknown` | sim | nao |
| `trf2_eproc_jurisprudencia` | nao | text, number | `unknown` | nao | nao |
| `trf3_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `trf4_eproc_jurisprudencia` | nao | text, number | `unknown` | nao | nao |
| `trf5_jurisprudencia` | nao | text, number, published_from, published_to, types | `unknown` | nao | nao |
| `trf6_eproc_jurisprudencia` | nao | text, number | `unknown` | nao | nao |
| `trt2_pje_jurisprudencia` | nao | - | `unknown` | nao | nao |
| `tst_jurisprudencia` | nao | text, all_words, any_words, without_words, exact_phrase, number, published_from, published_to, updated_from, updated_to, types | `offset` | sim | nao |
