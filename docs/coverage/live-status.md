# Live Status

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

Status live e uma fotografia de validacao, nao garantia de disponibilidade.
Chamadas a tribunais podem variar por rede, horario, WAF, captcha, TLS e
alteracao do proprio portal.

| Fonte | Status | Data | Retornados | Total Informado | Paginacao | Latencia | Observacao |
| --- | --- | --- | ---: | ---: | --- | ---: | --- |
| `bnp_pangea` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `cjf_jurisprudencia` | `blocked` | 2026-08-16 | 0 | - | `-` | 633.69 | CJF/TRF1 jurisprudence returned access-control HTML |
| `cnj_jurisprudencia` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `eproc_jurisprudencia_federal` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `falcao_jt` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `justica_eleitoral_sjur` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `stf_informativo` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `stf_juris` | `tls_verification_failed` | 2026-08-16 | 0 | - | `-` | 550.89 | STF jurisprudence API SSL verification failed in this environment. |
| `stj_dados_abertos_jurisprudencia` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `stj_informativo` | `valid` | 2026-08-16 | 1 | 12 | `local_window` | 4388.93 | A resposta e uma janela parcial do total informado pela fonte. |
| `stj_scon` | `valid` | 2026-08-16 | - | - | `-` | - | - |
| `stm_jurisprudencia` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `tce_sp_jurisprudencia` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `tcu_jurisprudencia` | `valid` | 2026-08-16 | 1 | 1 | `unknown` | 12803.23 | - |
| `tjac_cjsg` | `valid` | 2026-08-16 | - | - | `-` | - | - |
| `tjal_cjsg` | `valid` | 2026-08-16 | - | - | `-` | - | - |
| `tjam_cjsg` | `valid_with_source_page_limit` | 2026-08-16 | - | - | `-` | - | - |
| `tjap_tucujuris` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `tjba_graphql` | `valid` | 2026-08-16 | - | - | `-` | - | - |
| `tjce_cjsg` | `unknown` | 2026-08-16 | 0 | - | `-` | - | - |
| `tjce_informativos` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `tjce_sjuris` | `valid` | 2026-08-16 | 5 | 266 | `page` | - | - |
| `tjdf_juris` | `valid` | 2026-08-16 | 1 | 131875 | `page` | 2561.1 | A resposta e uma janela parcial do total informado pela fonte. |
| `tjes_jurisprudencia` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `tjgo_projudi_jurisprudencia` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `tjma_jurisconsult` | `valid` | 2026-08-16 | - | - | `-` | - | - |
| `tjmg_jurisprudencia` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `tjms_cjsg` | `valid` | 2026-08-16 | - | - | `-` | - | - |
| `tjmt_jurisprudencia_api` | `valid` | 2026-08-16 | 5 | 7578 | `page` | - | - |
| `tjpa_jurisprudencia_bff` | `valid` | 2026-08-16 | - | - | `-` | - | - |
| `tjpb_pje_jurisprudencia` | `valid` | 2026-08-16 | 1 | 25723 | `page` | 830.19 | A resposta e uma janela parcial do total informado pela fonte. |
| `tjpe_jurisprudencia` | `source_unavailable` | 2026-08-16 | - | - | `offset` | - | - |
| `tjpi_juspi` | `valid` | 2026-08-16 | 1 | 63468 | `page` | 2197.72 | A resposta e uma janela parcial do total informado pela fonte. |
| `tjpr_jurisprudencia` | `valid` | 2026-08-16 | - | - | `-` | - | - |
| `tjrj_eproc_jurisprudencia` | `valid` | 2026-08-16 | - | - | `-` | - | - |
| `tjrn_jurisprudencia` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `tjro_liame` | `valid` | 2026-08-16 | 1 | 1 | `-` | - | - |
| `tjrr_juris` | `source_pagination_not_validated` | 2026-08-16 | - | - | `-` | - | - |
| `tjrs_solr` | `valid` | 2026-08-16 | 1 | 692019 | `offset` | 797.85 | A resposta e uma janela parcial do total informado pela fonte. |
| `tjsc_eproc_jurisprudencia` | `valid` | 2026-08-16 | - | - | `-` | - | - |
| `tjse_jurisprudencia` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `tjsp_cjsg` | `access_controlled` | 2026-08-16 | - | - | `-` | - | - |
| `tjsp_eproc_jurisprudencia` | `access_controlled` | 2026-08-16 | - | - | `-` | - | - |
| `tjsp_nugepnac` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `tjto_jurisprudencia` | `access_controlled_or_inconclusive` | 2026-08-16 | - | - | `-` | - | - |
| `tnu_eproc_jurisprudencia` | `valid` | 2026-08-16 | 1 | 10 | `unknown` | 1235.89 | A rota observada retorna a primeira pagina, mas o contrato de paginação remota ainda não foi comprovado. |
| `tre_sp_temas` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `trf2_eproc_jurisprudencia` | `valid` | 2026-08-16 | 1 | 10 | `unknown` | 1509.35 | A rota observada retorna a primeira pagina, mas o contrato de paginação remota ainda não foi comprovado. |
| `trf3_jurisprudencia` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `trf4_eproc_jurisprudencia` | `valid` | 2026-08-16 | 1 | 10 | `unknown` | 2177.5 | - |
| `trf5_jurisprudencia` | `valid` | 2026-08-16 | 1 | 1 | `unknown` | 1118.15 | A resposta HTML observada representa a primeira pagina; o contrato de paginação remota ainda não foi promovido. |
| `trf6_eproc_jurisprudencia` | `valid` | 2026-08-16 | 1 | 10 | `unknown` | 2026.16 | A rota observada retorna a primeira pagina, mas o contrato de paginação remota ainda não foi comprovado. |
| `trt2_pje_jurisprudencia` | `not_checked_in_latest_focused_run` | - | - | - | `-` | - | sem validacao focada nesta rodada |
| `tst_jurisprudencia` | `valid` | 2026-08-16 | 1 | 841967 | `offset` | 1324.01 | A resposta e uma janela parcial do total informado pela fonte. |
