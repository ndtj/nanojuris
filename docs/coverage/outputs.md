# Outputs

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

| Fonte | Registros Canonicos | Tipos | Formatos | Campos | Inteiro Teor | Trace |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `bnp_pangea` | CanonicalPrecedent | precedent, linked_decision_metadata | json | 9 | sim | sim |
| `cjf_jurisprudencia` | CanonicalDecision | acordao, sumula, arguicao, decisao_monocratica | html | 12 | nao | sim |
| `cnj_jurisprudencia` | CanonicalDecision, CanonicalDocument | informativo_jurisprudencia | html, pdf | 4 | nao | sim |
| `eproc_jurisprudencia_federal` | - | - | - | 0 | nao | nao |
| `falcao_jt` | - | - | - | 0 | nao | nao |
| `justica_eleitoral_sjur` | - | - | - | 0 | nao | nao |
| `stf_informativo` | CanonicalDecision | informativo, acordao_resumido, tese_informativo | xlsx | 17 | nao | sim |
| `stf_juris` | CanonicalDecision | acordao | json | 13 | nao | sim |
| `stj_dados_abertos_jurisprudencia` | ProviderCatalog, CanonicalDecision, ResearchRun | acordao_espelho, integra_decisao, acordao_dje | json, csv, zip | 17 | nao | sim |
| `stj_informativo` | CanonicalDecision | informativo, nota_jurisprudencia | html | 9 | nao | sim |
| `stj_scon` | CanonicalDecision, CanonicalDocument | acordao | html, pdf | 9 | sim | sim |
| `stm_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao | html | 9 | sim | sim |
| `tce_sp_jurisprudencia` | CanonicalPrecedent | sumula, boletim_jurisprudencia | html | 6 | nao | sim |
| `tcu_jurisprudencia` | CanonicalDecision, CanonicalPrecedent | acordao, jurisprudencia_selecionada, sumula, boletim | csv, text/html | 5 | nao | sim |
| `tjac_cjsg` | CanonicalDecision, CanonicalDocument | acordao, homologation, decision | html | 12 | sim | sim |
| `tjal_cjsg` | CanonicalDecision, CanonicalDocument | acordao, homologation, decision | html | 12 | sim | sim |
| `tjam_cjsg` | CanonicalDecision, CanonicalDocument | acordao, homologation, decision | html | 12 | sim | sim |
| `tjap_tucujuris` | - | - | - | 0 | nao | nao |
| `tjba_graphql` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica | json, html, text | 12 | sim | sim |
| `tjce_cjsg` | CanonicalDecision, CanonicalDocument | acordao, homologation, decision | html | 12 | sim | sim |
| `tjce_informativos` | CanonicalDecision | informativo_item | html, pdf | 11 | nao | sim |
| `tjce_sjuris` | CanonicalDecision | acordao, decisao_monocratica, sumula | json, text, pdf | 12 | sim | sim |
| `tjdf_juris` | CanonicalDecision, CanonicalDocument | acordao, turma_recursal, tema, informativo | html | 10 | sim | sim |
| `tjes_jurisprudencia` | - | - | - | 0 | nao | nao |
| `tjgo_projudi_jurisprudencia` | CanonicalDecision | decisao, sentenca, acordao | html | 8 | nao | sim |
| `tjma_jurisconsult` | ProviderCatalog | acordao, decisao_monocratica, sentenca, sumula | json | 7 | nao | sim |
| `tjmg_jurisprudencia` | - | - | - | 0 | nao | nao |
| `tjms_cjsg` | CanonicalDecision, CanonicalDocument | acordao, homologation, decision | html | 12 | sim | sim |
| `tjmt_jurisprudencia_api` | CanonicalDecision | acordao, decisao_monocratica | json, html, text | 11 | sim | sim |
| `tjpa_jurisprudencia_bff` | CanonicalDecision | acordao, decisao_monocratica | json | 10 | sim | sim |
| `tjpb_pje_jurisprudencia` | CanonicalDecision, CanonicalDocument | jurisprudencia_pje, acordao, decisao | json, html | 5 | sim | sim |
| `tjpe_jurisprudencia` | CanonicalDecision | acordao, decisao | json, html | 9 | sim | sim |
| `tjpi_juspi` | CanonicalDecision, CanonicalDocument | acordao, decisao_terminativa, sumula | html | 11 | sim | sim |
| `tjpr_jurisprudencia` | CanonicalDecision | acordao, decisao_monocratica, decisao | html | 9 | nao | sim |
| `tjrj_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica, sumula, despacho, sentenca | html | 12 | sim | sim |
| `tjrn_jurisprudencia` | - | - | - | 0 | nao | nao |
| `tjro_liame` | CanonicalPrecedent | irdr, iac | json | 10 | nao | sim |
| `tjrr_juris` | CanonicalDecision, CanonicalDocument | acordao, monocratic_decision | html, text | 9 | sim | sim |
| `tjrs_solr` | CanonicalDecision | acordao, decisao, informativo | json | 8 | nao | sim |
| `tjsc_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica, sumula, despacho, sentenca | html | 12 | sim | sim |
| `tjse_jurisprudencia` | - | - | - | 0 | nao | nao |
| `tjsp_cjsg` | CanonicalDecision, CanonicalDocument | acordao, monocratic_decision, homologation | html | 13 | sim | sim |
| `tjsp_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | sentenca, acordao, decisao_monocratica | html | 12 | sim | sim |
| `tjsp_nugepnac` | CanonicalPrecedent | irdr, iac | html | 12 | nao | sim |
| `tjto_jurisprudencia` | CanonicalDecision | acordao, decisao_monocratica, sentenca | html | 11 | sim | sim |
| `tnu_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica, decisao_presidente | html | 12 | sim | sim |
| `tre_sp_temas` | CanonicalPrecedent | tema_selecionado | html, pdf | 4 | nao | sim |
| `trf2_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica, sumula, despacho, sentenca | html | 12 | sim | sim |
| `trf3_jurisprudencia` | - | - | - | 0 | nao | nao |
| `trf4_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao, despacho | html | 11 | sim | sim |
| `trf5_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica, informativo, sumula | html | 7 | sim | sim |
| `trf6_eproc_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao_monocratica, sumula, despacho, sentenca | html | 12 | sim | sim |
| `trt2_pje_jurisprudencia` | - | - | - | 0 | nao | nao |
| `tst_jurisprudencia` | CanonicalDecision, CanonicalDocument | acordao, decisao, sumula, precedente_normativo | json, html | 11 | sim | sim |
