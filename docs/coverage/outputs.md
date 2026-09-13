# Outputs

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

| Fonte | Registros Canonicos | Tipos | Formatos | Campos | Inteiro Teor | Trace |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `bnp_pangea` | CanonicalPrecedent | precedent, linked_decision_metadata | json | 9 | nao | sim |
| `cjf_jurisprudencia` | JurisprudenceResult, CanonicalDocument, DecisionBundle | acordao, sumula, arguicao, decisao_monocratica | html | 13 | sim | sim |
| `cnj_jurisprudencia` | CanonicalDecision, CanonicalDocument | informativo_jurisprudencia | html, pdf | 4 | sim | sim |
| `eproc_jurisprudencia_federal` | CanonicalDecision, CanonicalDocument | acordao, decisao, despacho | html | 11 | sim | sim |
| `falcao_jt` | CanonicalDecision | sentenca, acordao, decisao_monocratica, precedent | html, json | 12 | nao | sim |
| `justica_eleitoral_sjur` | ProviderCatalog | catalog_metadata | json | 4 | nao | sim |
| `stf_informativo` | CanonicalDecision | informativo, acordao_resumido, tese_informativo | xlsx | 18 | nao | sim |
| `stf_juris` | CanonicalDecision | acordao | json | 16 | nao | sim |
| `stj_dados_abertos_jurisprudencia` | ProviderCatalog, CanonicalDecision, ResearchRun | acordao_espelho, integra_decisao, acordao_dje | json, csv, zip | 32 | sim | sim |
| `stj_informativo` | CanonicalDecision, CanonicalDocument | informativo, nota_jurisprudencia | html | 10 | sim | sim |
| `stj_scon` | CanonicalDecision, CanonicalDocument | acordao | html, pdf | 9 | sim | sim |
| `stm_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao | html | 9 | sim | sim |
| `tce_pr_viajuris` | CanonicalDecision, CanonicalDocument | acordao | csv, pdf_link | 6 | sim | sim |
| `tce_sp_jurisprudencia` | CanonicalPrecedent, CanonicalDocument | sumula, boletim_jurisprudencia, indice_remissivo | html | 8 | sim | sim |
| `tcu_jurisprudencia` | CanonicalDecision, CanonicalPrecedent | acordao, jurisprudencia_selecionada, sumula, boletim | csv, text/html | 16 | nao | sim |
| `tjac_banco_sentencas` | CanonicalDecision, CanonicalDocument | sentenca | html, pdf, text | 9 | sim | sim |
| `tjac_cjsg` | CanonicalDecision, CanonicalDocument | acordao, homologation, decision | html | 12 | sim | sim |
| `tjac_ementario_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao_ementa | pdf, text | 14 | nao | sim |
| `tjal_cjsg` | CanonicalDecision, CanonicalDocument | acordao, homologation, decision | html | 12 | sim | sim |
| `tjal_esmal_banco_sentencas` | CanonicalDecision, CanonicalDocument | sentenca | html, pdf, text | 10 | sim | sim |
| `tjal_turma_recursal_ementario` | CanonicalDecision, CanonicalDocument | acordao_ementa, recurso_inominado, decisao | pdf, text | 14 | nao | sim |
| `tjam_cjsg` | CanonicalDecision, CanonicalDocument | acordao, homologation, decision | html | 12 | sim | sim |
| `tjap_banco_sentencas` | CanonicalDecision, CanonicalDocument | decisao, sentenca | html, text | 13 | sim | sim |
| `tjap_tucujuris` | CanonicalDecision | acordao | json | 8 | nao | sim |
| `tjba_graphql` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica | json, html, text | 12 | sim | sim |
| `tjce_cjsg` | CanonicalDecision, CanonicalDocument | acordao, homologation, decision | html | 12 | sim | sim |
| `tjce_informativos` | CanonicalDecision | informativo_item | html, pdf | 12 | nao | sim |
| `tjce_sjuris` | CanonicalDecision | acordao, decisao_monocratica, sumula | json, text, pdf | 12 | sim | sim |
| `tjdf_juris` | CanonicalDecision, CanonicalDocument | acordao, turma_recursal, tema, informativo | html, json | 10 | sim | sim |
| `tjes_cjpg` | CanonicalDecision | decisao_1g, sentenca | json, text, html | 14 | sim | sim |
| `tjes_jurisprudencia` | CanonicalDecision | acordao, decisao_monocratica | json, text, html | 12 | sim | sim |
| `tjes_turma_recursal` | CanonicalDecision | acordao, recurso_inominado | json, text | 11 | sim | sim |
| `tjgo_projudi_jurisprudencia` | CanonicalDecision | decisao, sentenca, acordao | html | 11 | sim | sim |
| `tjma_informativos` | CanonicalDecision, CanonicalDocument | informativo_jurisprudencia | html, pdf | 10 | sim | sim |
| `tjma_jurisconsult` | ProviderCatalog, JurisprudenceResult, SearchPage | acordao, decisao_monocratica, sentenca, sumula | json | 18 | nao | sim |
| `tjmg_dspace_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, ementa | json, pdf, text | 12 | sim | sim |
| `tjmg_ejef_boletim_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, ementa, boletim | json, pdf, text | 10 | sim | sim |
| `tjmg_jurisprudencia` | CanonicalDecision | acordao, decisao_monocratica, decisao_turma_recursal | json, html | 9 | sim | sim |
| `tjmmg_jurisprudencia_api` | CanonicalDecision, CanonicalDocument | acordao, decisao | json, pdf | 12 | sim | sim |
| `tjmrs_jurisprudencia` | JurisprudenceResult, CanonicalDocument | acordao | html | 12 | sim | sim |
| `tjms_cjpg` | CanonicalDecision | decisao_1g, sentenca | html, text | 13 | sim | sim |
| `tjms_cjsg` | CanonicalDecision, CanonicalDocument | acordao, homologation, decision | html | 12 | sim | sim |
| `tjmsp_jurisprudencia` | CanonicalDecision | acordao, decisao | html, pdf | 13 | nao | sim |
| `tjmt_jurisprudencia_api` | CanonicalDecision | acordao, decisao_monocratica | json, html, text | 11 | sim | sim |
| `tjpa_jurisprudencia_bff` | CanonicalDecision | acordao, decisao_monocratica | json | 10 | sim | sim |
| `tjpb_pje_jurisprudencia` | CanonicalDecision, CanonicalDocument | jurisprudencia_pje, acordao, decisao | json, html | 5 | sim | sim |
| `tjpe_jurisprudencia` | CanonicalDecision | acordao, decisao | json, html | 9 | sim | sim |
| `tjpi_juspi` | CanonicalDecision, CanonicalDocument | acordao, decisao_terminativa | html | 11 | sim | sim |
| `tjpr_jurisprudencia` | CanonicalDecision | acordao, decisao_monocratica, decisao | html | 9 | sim | sim |
| `tjrj_banco_sentencas` | CanonicalDecision, CanonicalDocument | sentenca | pdf, doc, docx, text | 10 | sim | sim |
| `tjrj_ejuris` | CanonicalDecision | acordao, decisao_monocratica | html, json | 10 | sim | sim |
| `tjrj_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica, sumula, despacho, sentenca | html | 12 | sim | sim |
| `tjrn_jurisprudencia` | CanonicalDecision | acordao, decisao_monocratica, sentenca | json, text | 15 | sim | sim |
| `tjro_jurisprudencia` | CanonicalDecision, CanonicalDocument | decision, sentence, vote, acordao | json, html, text, pdf, docx | 14 | sim | sim |
| `tjro_liame` | CanonicalPrecedent | irdr, iac | json | 10 | nao | sim |
| `tjrr_juris` | CanonicalDecision, CanonicalDocument | acordao, monocratic_decision | html, text | 9 | sim | sim |
| `tjrs_solr` | CanonicalDecision, CanonicalDocument | acordao, decisao, informativo, inteiro_teor_tiff | json, tiff | 9 | sim | sim |
| `tjsc_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica, sumula, despacho, sentenca | html | 12 | sim | sim |
| `tjse_boletim_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, ementa | html, text | 12 | sim | sim |
| `tjse_jurisprudencia` | CanonicalDecision | acordao, monocratic_decision | html, jsf | 8 | nao | sim |
| `tjsp_cjpg` | CanonicalDecision | decisao_1g, sentenca | html, text | 13 | sim | sim |
| `tjsp_cjsg` | CanonicalDecision, CanonicalDocument | acordao, monocratic_decision, homologation | html | 13 | sim | sim |
| `tjsp_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | sentenca, acordao, decisao_monocratica | html | 12 | sim | sim |
| `tjsp_nugepnac` | CanonicalPrecedent | irdr, iac | html | 24 | nao | sim |
| `tjto_jurisprudencia` | CanonicalDecision | acordao, decisao_monocratica, sentenca | html | 11 | sim | sim |
| `tnu_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica, decisao_presidente | html | 12 | sim | sim |
| `tre_sjur_first_degree` | JurisprudenceResult | sentenca | json, html | 11 | sim | sim |
| `tre_sjur_jurisprudencia` | JurisprudenceResult | acordao, decisao, resolucao | json, html | 11 | sim | sim |
| `tre_sp_temas` | CanonicalPrecedent | tema_selecionado | html, pdf | 4 | sim | sim |
| `trf2_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica, sumula, despacho, sentenca | html | 12 | sim | sim |
| `trf3_jurisprudencia` | JurisprudenceResult, CanonicalDocument | acordao | html | 9 | sim | sim |
| `trf4_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao, despacho | html | 11 | sim | sim |
| `trf5_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica, informativo, sumula | html | 7 | sim | sim |
| `trf6_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica, sumula, despacho, sentenca | html | 12 | sim | sim |
| `trt15_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao_ementa, acordao_full_text | json, html | 10 | sim | sim |
| `trt2_basis_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao_ementa, boletim_jurisprudencia | html, pdf, text | 10 | sim | sim |
| `trt2_ementario_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao_ementa | html, pdf, text | 11 | sim | sim |
| `trt2_pje_jurisprudencia` | JurisprudenceResult | acordao, decisao | json, html | 9 | nao | sim |
| `trt3_ementario_jurisprudencia` | CanonicalDecision, CanonicalDocument | ementario, acordao_ementa | pdf, text | 9 | nao | sim |
| `trt4_sumulas_jurisprudencia` | CanonicalDecision, CanonicalDocument | sumula, orientacao_jurisprudencial, acordao | html, pdf, text | 9 | nao | sim |
| `trt6_jurisprudencia` | JurisprudenceResult | acordao | json, html | 13 | sim | sim |
| `trt8_pje_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao | json, html | 14 | sim | sim |
| `trt9_nugepnac_jurisprudencia` | CanonicalDecision, CanonicalDocument | precedente_qualificado, ementa | pdf, text | 9 | nao | sim |
| `tse_sjur_jurisprudencia` | JurisprudenceResult | acordao, decisao | json, html | 11 | sim | sim |
| `tst_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao, sumula, precedente_normativo | json, html | 11 | sim | sim |
