# Live Status

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

Status live e uma fotografia de validacao, nao garantia de disponibilidade.
Chamadas a tribunais podem variar por rede, horario, WAF, captcha, TLS e
alteracao do proprio portal.

| Fonte | Status | Data | Retornados | Total Informado | Paginacao | Latencia | Observacao |
| --- | --- | --- | ---: | ---: | --- | ---: | --- |
| `bnp_pangea` | `valid` | 2026-09-09 | 1 | 1 | `page` | - | bounded dedicated provider check |
| `cjf_jurisprudencia` | `access_control_required` | 2026-09-07 | - | - | `offset` | - | bounded dedicated provider check |
| `cnj_jurisprudencia` | `valid` | 2026-09-05 | 2 | 10 | `page` | - | bounded dedicated provider check |
| `eproc_jurisprudencia_federal` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `falcao_jt` | `access_control_required` | 2026-09-11 | - | - | `offset` | - | bounded dedicated provider check |
| `justica_eleitoral_sjur` | `source_unavailable` | 2026-09-07 | - | - | `offset` | - | bounded dedicated provider check |
| `stf_informativo` | `source_unavailable` | 2026-09-07 | - | - | `offset` | - | bounded dedicated provider check |
| `stf_juris` | `blocked_transport` | 2026-09-01 | 0 | - | `offset` | - | bounded dedicated provider check |
| `stj_dados_abertos_jurisprudencia` | `valid` | 2026-09-06 | 11 | 11 | `offset` | - | bounded dedicated provider check |
| `stj_informativo` | `valid` | 2026-09-05 | 1 | 11 | `local_window` | 2794.1 | A resposta e uma janela parcial do total informado pela fonte. |
| `stj_scon` | `access_control_required` | 2026-09-07 | - | - | `offset` | - | bounded dedicated provider check |
| `stm_jurisprudencia` | `valid` | 2026-09-08 | 2 | 2597 | `offset` | - | bounded dedicated provider check |
| `tce_pr_viajuris` | `valid` | 2026-09-05 | 1 | 1 | `local_window` | 2032.36 | A janela retornada alcanca o total informado pela fonte. |
| `tce_sp_jurisprudencia` | `empty_unconfirmed` | 2026-09-05 | 0 | 0 | `unknown` | 826.31 | - |
| `tcu_jurisprudencia` | `valid` | 2026-09-05 | 1 | 1 | `unknown` | 19562.36 | - |
| `tjac_banco_sentencas` | `valid` | 2026-09-12 | 2 | - | `local_html_window` | - | bounded dedicated provider check |
| `tjac_cjsg` | `valid` | 2026-09-08 | 1 | 18299 | `page` | - | bounded dedicated provider check |
| `tjac_ementario_jurisprudencia` | `valid` | 2026-09-08 | 7 | - | `local_pdf_window` | 1328.1 | bounded dedicated provider check |
| `tjal_cjsg` | `valid` | 2026-09-08 | 1 | 159266 | `page` | - | bounded dedicated provider check |
| `tjal_esmal_banco_sentencas` | `valid` | 2026-09-09 | - | - | `page` | - | bounded dedicated provider check |
| `tjal_turma_recursal_ementario` | `public_textual_recursal` | 2026-09-08 | 29 | - | `local_pdf_window` | - | bounded dedicated provider check |
| `tjam_cjsg` | `valid` | 2026-09-13 | 1 | 749 | `page` | - | bounded dedicated provider check; detalhe oficial bloqueado por CAPTCHA, busca permanece valida |
| `tjap_banco_sentencas` | `valid` | 2026-09-13 | 1 | 10000 | `livewire_page` | - | bounded dedicated provider check |
| `tjap_tucujuris` | `access_controlled` | 2026-09-13 | - | - | `offset` | - | bounded dedicated provider check |
| `tjba_graphql` | `valid` | 2026-09-08 | 1 | - | `page` | - | bounded dedicated provider check |
| `tjce_cjsg` | `valid` | 2026-09-13 | 1 | 107097 | `page` | - | bounded dedicated provider check; inteiro teor PDF validado em chamada bounded |
| `tjce_informativos` | `valid` | 2026-09-07 | 1 | 10 | `offset` | - | bounded dedicated provider check |
| `tjce_sjuris` | `valid` | 2026-09-10 | 1 | 42009 | `page` | 1454.4 | bounded dedicated provider check |
| `tjdf_juris` | `valid` | 2026-09-08 | 1 | - | `page` | - | bounded dedicated provider check |
| `tjes_cjpg` | `valid` | 2026-09-09 | 1 | 977546 | `page` | - | bounded dedicated provider check |
| `tjes_jurisprudencia` | `valid` | 2026-09-08 | 1 | 155766 | `page` | - | bounded dedicated provider check |
| `tjes_turma_recursal` | `valid` | 2026-09-06 | 1 | 39182 | `offset` | - | bounded dedicated provider check |
| `tjgo_projudi_jurisprudencia` | `valid` | 2026-09-10 | 1 | 19743 | `page` | 4957.34 | bounded dedicated provider check |
| `tjma_informativos` | `valid` | 2026-09-08 | 8 | - | `local_window` | - | bounded dedicated provider check |
| `tjma_jurisconsult` | `access_controlled` | 2026-09-13 | - | - | `offset` | - | bounded dedicated provider check |
| `tjmg_dspace_jurisprudencia` | `valid` | 2026-09-06 | 1 | 185 | `merged_collection_page` | - | bounded dedicated provider check |
| `tjmg_ejef_boletim_jurisprudencia` | `valid` | 2026-09-09 | 1 | 2 | `offset` | - | bounded dedicated provider check |
| `tjmg_jurisprudencia` | `valid` | 2026-09-13 | 1 | 1000 | `page` | 395.75 | bounded dedicated provider check |
| `tjmmg_jurisprudencia_api` | `valid` | 2026-09-11 | 1 | 1 | `none` | - | bounded dedicated provider check |
| `tjmrs_jurisprudencia` | `valid` | 2026-09-09 | 1 | 1 | `none` | - | bounded dedicated provider check |
| `tjms_cjpg` | `valid` | 2026-09-09 | 1 | 317418 | `page` | - | bounded dedicated provider check |
| `tjms_cjsg` | `valid` | 2026-09-08 | 1 | 230516 | `page` | - | bounded dedicated provider check |
| `tjmsp_jurisprudencia` | `access_control_required` | 2026-09-10 | - | - | `offset` | - | bounded dedicated provider check |
| `tjmt_jurisprudencia_api` | `valid` | 2026-09-08 | 1 | 74118 | `page` | - | bounded dedicated provider check |
| `tjpa_jurisprudencia_bff` | `valid` | 2026-09-08 | 1 | 10000 | `page` | - | bounded dedicated provider check |
| `tjpb_pje_jurisprudencia` | `valid` | 2026-09-08 | 1 | 26092 | `page` | - | bounded dedicated provider check |
| `tjpe_jurisprudencia` | `valid` | 2026-09-08 | 1 | - | `page` | - | bounded dedicated provider check |
| `tjpi_juspi` | `valid` | 2026-09-08 | 1 | 33404 | `page` | - | bounded dedicated provider check |
| `tjpr_jurisprudencia` | `valid` | 2026-09-08 | 1 | 1004007 | `page` | - | bounded dedicated provider check |
| `tjrj_banco_sentencas` | `partial` | 2026-09-08 | - | - | `local_window` | - | bounded dedicated provider check |
| `tjrj_ejuris` | `valid` | 2026-09-10 | 1 | 46191 | `page` | - | bounded dedicated provider check |
| `tjrj_eproc_jurisprudencia` | `valid` | 2026-09-13 | - | - | `offset` | - | bounded dedicated provider check |
| `tjrn_jurisprudencia` | `valid` | 2026-09-09 | 1 | 53930 | `page` | - | bounded dedicated provider check |
| `tjro_jurisprudencia` | `valid` | 2026-09-09 | 1 | 1908815 | `offset` | - | bounded dedicated provider check |
| `tjro_liame` | `valid` | 2026-09-05 | 1 | 1 | `page` | - | bounded dedicated provider check |
| `tjrr_juris` | `valid` | 2026-09-13 | 10 | 14238 | `page` | - | bounded dedicated provider check |
| `tjrs_solr` | `valid` | 2026-09-08 | 1 | 706568 | `page` | - | bounded dedicated provider check |
| `tjsc_eproc_jurisprudencia` | `valid` | 2026-09-08 | - | - | `offset` | - | bounded dedicated provider check |
| `tjse_boletim_jurisprudencia` | `valid` | 2026-09-07 | 10 | - | `edition_section` | 18532.84 | bounded dedicated provider check |
| `tjse_jurisprudencia` | `blocked_access_control_no_reproducible_result` | 2026-09-06 | - | - | `offset` | - | bounded dedicated provider check |
| `tjsp_cjpg` | `valid` | 2026-09-02 | 1 | 4660092 | `page` | - | bounded dedicated provider check |
| `tjsp_cjsg` | `valid` | 2026-09-13 | 1 | 870 | `page` | - | bounded dedicated provider check |
| `tjsp_eproc_jurisprudencia` | `valid` | 2026-09-05 | 2 | 297135 | `page` | - | bounded dedicated provider check |
| `tjsp_nugepnac` | `reachable_empty_data` | 2026-09-07 | 0 | 0 | `offset` | - | bounded dedicated provider check |
| `tjto_jurisprudencia` | `valid` | 2026-09-09 | 1 | 137636 | `page` | - | bounded dedicated provider check |
| `tnu_eproc_jurisprudencia` | `valid` | 2026-09-10 | 1 | 11228 | `page` | - | bounded dedicated provider check |
| `tre_sjur_first_degree` | `valid` | 2026-09-12 | 1000 | 10000 | `none` | - | filtro remoto de tipo de decisao observado em 27 TREs; 1 janela(s) com registros, 26 vazio(s) autoritativo(s), 0 resposta(s) nao classificadas; paginacao e inteiro teor pendentes; busca textual sem filtro retornou somente segundo grau; filtro de tipo permanece obrigatório |
| `tre_sjur_jurisprudencia` | `partial` | 2026-09-12 | 1000 | 2119 | `none` | 4734.91 | sonda oficial comparou pagina 0 e 1 e recebeu a mesma janela; paginaÃ§ao remota permanece nao comprovada; PDF publico validado para um registro observado; particao mensal de data validada em intervalo bounded |
| `tre_sp_temas` | `source_unavailable` | 2026-09-05 | 0 | - | `-` | 890.8 | TRE-SP temas rejected request with HTTP 403 |
| `trf2_eproc_jurisprudencia` | `valid` | 2026-09-10 | 1 | 228086 | `page` | - | bounded dedicated provider check |
| `trf3_jurisprudencia` | `transport_error` | 2026-09-09 | - | - | `offset` | - | bounded dedicated provider check |
| `trf4_eproc_jurisprudencia` | `valid` | 2026-09-08 | 2 | 477848 | `page` | - | bounded dedicated provider check |
| `trf5_jurisprudencia` | `valid` | 2026-09-08 | 1 | - | `page` | - | bounded dedicated provider check |
| `trf6_eproc_jurisprudencia` | `valid` | 2026-09-10 | 1 | 69677 | `page` | - | bounded dedicated provider check |
| `trt15_jurisprudencia` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `trt2_basis_jurisprudencia` | `partial` | 2026-09-07 | 0 | - | `offset` | - | bounded dedicated provider check |
| `trt2_ementario_jurisprudencia` | `valid` | 2026-09-08 | 2 | - | `local_window` | - | bounded dedicated provider check |
| `trt2_pje_jurisprudencia` | `access_control_required` | 2026-09-10 | 0 | 40245100 | `offset_unverified` | - | bounded dedicated provider check |
| `trt3_ementario_jurisprudencia` | `valid` | 2026-09-10 | 9 | 9 | `local_pdf_window` | - | bounded dedicated provider check |
| `trt4_sumulas_jurisprudencia` | `valid_curated_context` | 2026-09-10 | 212 | 212 | `local_html_window` | - | bounded dedicated provider check |
| `trt6_jurisprudencia` | `valid` | 2026-09-12 | 10 | 77585 | `offset` | - | bounded dedicated provider check |
| `trt8_pje_jurisprudencia` | `valid` | 2026-09-09 | 10 | 46181 | `page` | - | bounded dedicated provider check |
| `trt9_nugepnac_jurisprudencia` | `valid_curated_context` | 2026-09-10 | 25 | 25 | `local_pdf_window` | - | bounded dedicated provider check |
| `tse_sjur_jurisprudencia` | `valid` | 2026-09-12 | 3 | 10000 | `none` | - | bounded dedicated provider check |
| `tst_jurisprudencia` | `valid` | 2026-09-07 | 1 | 849232 | `offset` | - | bounded dedicated provider check |
