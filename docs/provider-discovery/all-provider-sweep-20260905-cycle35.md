# Sweep live de todos os providers

Gerado em `2026-09-05T08:00:03+00:00`; modo `live_bounded`; providers: **52**.

## Resumo

- Observados: **52**; sem observação: **0**.
- Rotas declaradas: **148**; candidatas observadas: **1962**.
- Filtros declarados: **277**; campos observados: **192**.
- Providers com sinais de controle de acesso: **10**.

## Matriz de maturação da evidência

| Provider | Observações | Status | Rotas | Filtros | TODO principal |
| --- | ---: | --- | ---: | ---: | --- |
| `bnp_pangea` | 1 | empty:1 | 0 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `cjf_jurisprudencia` | 1 | valid:1 | 19 | 2 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `cnj_jurisprudencia` | 1 | valid:1 | 28 | 8 | capturar e validar GETs declarados ainda não observados |
| `justica_eleitoral_sjur` | 1 | valid:1 | 9 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `stf_informativo` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `stf_juris` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `stj_dados_abertos_jurisprudencia` | 1 | valid:1 | 43 | 1 | capturar e validar GETs declarados ainda não observados |
| `stj_informativo` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `stj_scon` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `stm_jurisprudencia` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tce_pr_viajuris` | 1 | valid:1 | 30 | 35 | capturar e validar GETs declarados ainda não observados |
| `tce_sp_jurisprudencia` | 1 | valid:1 | 137 | 1 | capturar e validar GETs declarados ainda não observados |
| `tcu_jurisprudencia` | 1 | candidate:1 | 3 | 0 | capturar e validar GETs declarados ainda não observados |
| `tjac_cjsg` | 1 | valid:1 | 68 | 5 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjal_cjsg` | 1 | valid:1 | 76 | 4 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjam_cjsg` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjba_graphql` | 1 | empty:1 | 0 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjce_cjsg` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjce_informativos` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjce_sjuris` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjdf_juris` | 1 | candidate:1 | 0 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjes_cjpg` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjes_jurisprudencia` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjes_turma_recursal` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjgo_projudi_jurisprudencia` | 1 | access_controlled:1 | 83 | 6 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjma_jurisconsult` | 1 | candidate:1 | 7 | 0 | capturar e validar GETs declarados ainda não observados |
| `tjms_cjsg` | 1 | valid:1 | 99 | 5 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjmt_jurisprudencia_api` | 1 | candidate:1 | 8 | 0 | capturar e validar GETs declarados ainda não observados |
| `tjpa_jurisprudencia_bff` | 1 | valid:1 | 6 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjpb_pje_jurisprudencia` | 1 | valid:1 | 16 | 10 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjpe_jurisprudencia` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjpi_juspi` | 1 | candidate:1 | 6 | 1 | capturar e validar GETs declarados ainda não observados |
| `tjpr_jurisprudencia` | 1 | empty:1 | 1 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjrj_eproc_jurisprudencia` | 1 | redirect_outside_allowlist:1 | 0 | 0 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjrn_jurisprudencia` | 1 | valid:1 | 50 | 1 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjro_jurisprudencia` | 1 | empty:1 | 0 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjro_liame` | 1 | access_controlled:1 | 31 | 5 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjrr_juris` | 1 | valid:1 | 32 | 18 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjrs_solr` | 1 | valid:1 | 428 | 68 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjsc_eproc_jurisprudencia` | 1 | source_unavailable:1 | 0 | 0 | reproduzir indisponibilidade e criar teste de falha explícito |
| `tjsp_cjpg` | 1 | access_controlled:1 | 11 | 0 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjsp_cjsg` | 1 | valid:1 | 98 | 7 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjsp_eproc_jurisprudencia` | 1 | access_controlled:1 | 110 | 3 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjsp_nugepnac` | 1 | valid:1 | 218 | 0 | capturar e validar GETs declarados ainda não observados |
| `tjto_jurisprudencia` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tnu_eproc_jurisprudencia` | 1 | redirect_outside_allowlist:1 | 0 | 0 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tre_sp_temas` | 1 | access_controlled:1 | 0 | 0 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `trf2_eproc_jurisprudencia` | 1 | access_controlled:1 | 114 | 4 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `trf4_eproc_jurisprudencia` | 1 | access_controlled:1 | 112 | 4 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `trf5_jurisprudencia` | 1 | candidate:1 | 1 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `trf6_eproc_jurisprudencia` | 1 | access_controlled:1 | 118 | 4 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tst_jurisprudencia` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |

## Interpretação

Este artefato é evidência de discovery, não promoção automática de parser.
POSTs não foram submetidos sem payload contratado. Bloqueios, robots, SSO, rate limit, timeout e indisponibilidade permanecem estados explícitos.

O JSON contém hashes, rotas, filtros, comparação de contrato e TODOs por provider.

## Candidates do catálogo sem adapter runtime

| Source | Status live | Observações | Próximo passo |
| --- | --- | ---: | --- |
| `falcao_jt` | observed | 1 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `tjap_tucujuris` | observed | 1 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `tjmg_jurisprudencia` | observed | 1 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `tjrj_ejuris` | observed | 1 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `tjse_jurisprudencia` | observed | 1 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `trf3_jurisprudencia` | observed | 1 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `trt2_pje_jurisprudencia` | observed | 1 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
