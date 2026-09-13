# Inventário de capacidades documentais

Gerado offline por `python tools/build_document_capability_inventory.py --write`.
As declarações não significam disponibilidade live, autorização de reuso ou promoção.

Fontes: **85**; runtime: **80**; runtime com inteiro teor: **66**; candidatas: **5**; runtime opt-in: **5**.

| Provider | Ciclo de vida | Runtime | Inteiro teor | Formatos | Rotas documentais | Acesso |
| --- | --- | :---: | :---: | --- | ---: | --- |
| `bnp_pangea` | `implemented` | sim | não | json | 4 | `not_available` |
| `cjf_jurisprudencia` | `implemented` | sim | sim | html | 2 | `detail_call` |
| `cnj_jurisprudencia` | `implemented` | sim | sim | html, pdf | 2 | `document_link` |
| `eproc_jurisprudencia_federal` | `implemented` | sim | sim | html | 2 | `detail_call` |
| `falcao_jt` | `candidate` | opt-in | não | html, json | 6 | `unknown` |
| `justica_eleitoral_sjur` | `implemented` | sim | não | json | 4 | `not_available` |
| `stf_informativo` | `implemented` | sim | não | xlsx | 1 | `not_available` |
| `stf_juris` | `implemented` | sim | não | json | 1 | `link_only` |
| `stj_dados_abertos_jurisprudencia` | `implemented` | sim | sim | json, csv, zip | 4 | `detail_call` |
| `stj_informativo` | `implemented` | sim | sim | html | 1 | `document_link` |
| `stj_scon` | `implemented` | sim | sim | html, pdf | 5 | `detail_call` |
| `stm_jurisprudencia` | `implemented` | sim | sim | html | 2 | `detail_call` |
| `tce_pr_viajuris` | `implemented` | sim | sim | csv, pdf_link | 1 | `document_link` |
| `tce_sp_jurisprudencia` | `implemented` | sim | sim | html | 3 | `document_link` |
| `tcu_jurisprudencia` | `implemented` | sim | não | csv, text/html | 6 | `inline_summary` |
| `tjac_banco_sentencas` | `implemented` | sim | sim | html, pdf, text | 2 | `document_link` |
| `tjac_cjsg` | `implemented` | sim | sim | html | 3 | `detail_call` |
| `tjac_ementario_jurisprudencia` | `implemented` | sim | não | pdf, text | 1 | `summary_only` |
| `tjal_cjsg` | `implemented` | sim | sim | html | 3 | `detail_call` |
| `tjal_esmal_banco_sentencas` | `implemented` | sim | sim | html, pdf, text | 2 | `document_link` |
| `tjal_turma_recursal_ementario` | `implemented` | sim | não | pdf, text | 2 | `summary_only` |
| `tjam_cjsg` | `implemented` | sim | sim | html | 3 | `detail_call` |
| `tjap_banco_sentencas` | `implemented` | sim | sim | html, text | 3 | `inline` |
| `tjap_tucujuris` | `candidate` | opt-in | não | json | 3 | `access_blocked` |
| `tjba_graphql` | `implemented` | sim | sim | json, html, text | 3 | `detail_call` |
| `tjce_cjsg` | `implemented` | sim | sim | html | 3 | `detail_call` |
| `tjce_informativos` | `implemented` | sim | não | html, pdf | 1 | `not_available` |
| `tjce_sjuris` | `implemented` | sim | sim | json, text, pdf | 2 | `inline` |
| `tjdf_juris` | `implemented` | sim | sim | html, json | 4 | `detail_call` |
| `tjes_cjpg` | `implemented` | sim | sim | json, text, html | 1 | `inline` |
| `tjes_jurisprudencia` | `implemented` | sim | sim | json, text, html | 1 | `inline` |
| `tjes_turma_recursal` | `implemented` | sim | sim | json, text | 1 | `inline` |
| `tjgo_projudi_jurisprudencia` | `implemented` | sim | sim | html | 3 | `inline_result_text` |
| `tjma_informativos` | `implemented` | sim | sim | html, pdf | 2 | `document_link` |
| `tjma_jurisconsult` | `implemented` | sim | não | json | 11 | `access_blocked` |
| `tjmg_dspace_jurisprudencia` | `implemented` | sim | sim | json, pdf, text | 4 | `document_link` |
| `tjmg_ejef_boletim_jurisprudencia` | `implemented` | sim | sim | json, pdf, text | 4 | `document_link` |
| `tjmg_jurisprudencia` | `implemented` | sim | sim | json, html | 4 | `detail_call` |
| `tjmmg_jurisprudencia_api` | `implemented` | sim | sim | json, pdf | 2 | `inline` |
| `tjmrs_jurisprudencia` | `implemented` | sim | sim | html | 1 | `inline` |
| `tjms_cjpg` | `implemented` | sim | sim | html, text | 2 | `inline` |
| `tjms_cjsg` | `implemented` | sim | sim | html | 3 | `detail_call` |
| `tjmsp_jurisprudencia` | `candidate` | opt-in | não | html, pdf | 3 | `unknown` |
| `tjmt_jurisprudencia_api` | `implemented` | sim | sim | json, html, text | 3 | `inline` |
| `tjpa_jurisprudencia_bff` | `implemented` | sim | sim | json | 4 | `inline` |
| `tjpb_pje_jurisprudencia` | `implemented` | sim | sim | json, html | 7 | `detail_call` |
| `tjpe_jurisprudencia` | `implemented` | sim | sim | json, html | 9 | `inline` |
| `tjpi_juspi` | `implemented` | sim | sim | html | 3 | `detail_call` |
| `tjpr_jurisprudencia` | `implemented` | sim | sim | html | 3 | `document_link` |
| `tjrj_banco_sentencas` | `implemented` | sim | sim | pdf, doc, docx, text | 2 | `document_link` |
| `tjrj_ejuris` | `implemented` | sim | sim | html, json | 3 | `inline_result_text` |
| `tjrj_eproc_jurisprudencia` | `implemented` | sim | sim | html | 2 | `detail_call` |
| `tjrn_jurisprudencia` | `implemented` | sim | sim | json, text | 1 | `inline` |
| `tjro_jurisprudencia` | `implemented` | sim | sim | json, html, text, pdf, docx | 3 | `detail_call` |
| `tjro_liame` | `implemented` | sim | não | json | 2 | `not_offered_by_source` |
| `tjrr_juris` | `implemented` | sim | sim | html, text | 5 | `detail_call` |
| `tjrs_solr` | `implemented` | sim | sim | json, tiff | 2 | `detail_call` |
| `tjsc_eproc_jurisprudencia` | `implemented` | sim | sim | html | 2 | `detail_call` |
| `tjse_boletim_jurisprudencia` | `implemented` | sim | sim | html, text | 3 | `inline` |
| `tjse_jurisprudencia` | `candidate` | opt-in | não | html, jsf | 2 | `access_blocked` |
| `tjsp_cjpg` | `implemented` | sim | sim | html, text | 2 | `inline` |
| `tjsp_cjsg` | `implemented` | sim | sim | html | 3 | `detail_call` |
| `tjsp_eproc_jurisprudencia` | `implemented` | sim | sim | html | 2 | `detail_call` |
| `tjsp_nugepnac` | `implemented` | sim | não | html | 3 | `link_only` |
| `tjto_jurisprudencia` | `implemented` | sim | sim | html | 3 | `detail_call` |
| `tnu_eproc_jurisprudencia` | `implemented` | sim | sim | html | 2 | `detail_call` |
| `tre_sjur_first_degree` | `implemented` | sim | sim | json, html | 2 | `inline` |
| `tre_sjur_jurisprudencia` | `implemented` | sim | sim | json, html | 2 | `inline` |
| `tre_sp_temas` | `implemented` | sim | sim | html, pdf | 2 | `document_link` |
| `trf2_eproc_jurisprudencia` | `implemented` | sim | sim | html | 2 | `detail_call` |
| `trf3_jurisprudencia` | `implemented` | sim | sim | html | 2 | `detail_call` |
| `trf4_eproc_jurisprudencia` | `implemented` | sim | sim | html | 2 | `detail_call` |
| `trf5_jurisprudencia` | `implemented` | sim | sim | html | 3 | `detail_call` |
| `trf6_eproc_jurisprudencia` | `implemented` | sim | sim | html | 2 | `detail_call` |
| `trt15_jurisprudencia` | `implemented` | sim | sim | json, html | 5 | `detail_call` |
| `trt2_basis_jurisprudencia` | `implemented` | sim | sim | html, pdf, text | 3 | `document_link` |
| `trt2_ementario_jurisprudencia` | `implemented` | sim | sim | html, pdf, text | 4 | `document_link` |
| `trt2_pje_jurisprudencia` | `candidate` | opt-in | não | json, html | 3 | `access_blocked` |
| `trt3_ementario_jurisprudencia` | `implemented` | sim | não | pdf, text | 1 | `document_link` |
| `trt4_sumulas_jurisprudencia` | `implemented` | sim | não | html, pdf, text | 1 | `document_link` |
| `trt6_jurisprudencia` | `implemented` | sim | sim | json, html | 5 | `inline_result_text` |
| `trt8_pje_jurisprudencia` | `implemented` | sim | sim | json, html | 4 | `detail_call` |
| `trt9_nugepnac_jurisprudencia` | `implemented` | sim | não | pdf, text | 1 | `document_link` |
| `tse_sjur_jurisprudencia` | `implemented` | sim | sim | json, html | 2 | `inline` |
| `tst_jurisprudencia` | `implemented` | sim | sim | json, html | 9 | `detail_call` |

## Política

Busca não baixa documentos automaticamente. O carregamento de inteiro teor exige
rota HTTPS allowlisted, limite de bytes, hash, `SourceTrace` e classificação explícita
de acesso. Providers candidatos ficam fora da federação até contrato e revisão legal.
