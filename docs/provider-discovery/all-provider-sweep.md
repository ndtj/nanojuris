# Sweep live de todos os providers

Gerado em `2026-08-20T06:35:41+00:00`; modo `live_bounded`; providers: **44**.

## Resumo

- Observados: **44**; sem observação: **0**.
- Rotas declaradas: **129**; candidatas observadas: **3169**.
- Filtros declarados: **237**; campos observados: **299**.
- Providers com sinais de controle de acesso: **11**.

## Matriz de maturação da evidência

| Provider | Observações | Status | Rotas | Filtros | TODO principal |
| --- | ---: | --- | ---: | ---: | --- |
| `bnp_pangea` | 4 | empty:2, valid:2 | 0 | 1 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `cjf_jurisprudencia` | 2 | valid:2 | 26 | 9 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `cnj_jurisprudencia` | 3 | valid:1, empty:2 | 30 | 8 | nenhum TODO automático |
| `stf_informativo` | 2 | robots_disallowed:2 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `stf_juris` | 1 | robots_disallowed:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `stj_dados_abertos_jurisprudencia` | 4 | valid:1, robots_disallowed:2, empty:1 | 43 | 1 | revisar robots.txt e agendar nova coleta autorizada |
| `stj_informativo` | 2 | robots_disallowed:2 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `stj_scon` | 5 | robots_disallowed:5 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `stm_jurisprudencia` | 3 | robots_disallowed:2, valid:1 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tce_sp_jurisprudencia` | 4 | valid:1, empty:3 | 146 | 1 | nenhum TODO automático |
| `tcu_jurisprudencia` | 4 | candidate:1, valid:2, access_controlled:1 | 46 | 0 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjac_cjsg` | 3 | valid:2, empty:1 | 83 | 9 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjal_cjsg` | 3 | valid:2, empty:1 | 82 | 8 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjam_cjsg` | 3 | robots_disallowed:3 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjba_graphql` | 2 | empty:2 | 0 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjce_cjsg` | 3 | robots_disallowed:3 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjce_informativos` | 2 | valid:1, empty:1 | 346 | 16 | nenhum TODO automático |
| `tjce_sjuris` | 2 | valid:2 | 11 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjdf_juris` | 4 | candidate:4 | 34 | 0 | capturar fixture de formulário/JSON para confirmar filtros |
| `tjgo_projudi_jurisprudencia` | 2 | access_controlled:1, valid:1 | 96 | 6 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjma_jurisconsult` | 5 | candidate:1, empty:4 | 7 | 0 | capturar e validar GETs declarados ainda não observados |
| `tjms_cjsg` | 3 | valid:2, empty:1 | 99 | 5 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjmt_jurisprudencia_api` | 4 | candidate:3, access_controlled:1 | 23 | 0 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjpa_jurisprudencia_bff` | 3 | valid:2, source_unavailable:1 | 7 | 1 | reproduzir indisponibilidade e criar teste de falha explícito |
| `tjpb_pje_jurisprudencia` | 5 | valid:3, source_unavailable:2 | 17 | 10 | reproduzir indisponibilidade e criar teste de falha explícito |
| `tjpe_jurisprudencia` | 5 | robots_disallowed:5 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjpi_juspi` | 4 | candidate:1, valid:2, empty:1 | 6 | 7 | nenhum TODO automático |
| `tjpr_jurisprudencia` | 2 | empty:1, valid:1 | 203 | 49 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjrj_eproc_jurisprudencia` | 2 | robots_disallowed:2 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjro_liame` | 2 | access_controlled:1, empty:1 | 31 | 5 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjrr_juris` | 3 | valid:2, source_unavailable:1 | 32 | 18 | reproduzir indisponibilidade e criar teste de falha explícito |
| `tjrs_solr` | 2 | valid:1, robots_disallowed:1 | 426 | 69 | revisar robots.txt e agendar nova coleta autorizada |
| `tjsc_eproc_jurisprudencia` | 2 | access_controlled:2 | 202 | 11 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjsp_cjsg` | 3 | valid:2, empty:1 | 98 | 7 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjsp_eproc_jurisprudencia` | 2 | access_controlled:2 | 196 | 3 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjsp_nugepnac` | 4 | valid:2, candidate:2 | 218 | 0 | capturar fixture de formulário/JSON para confirmar filtros |
| `tjto_jurisprudencia` | 3 | robots_disallowed:3 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tnu_eproc_jurisprudencia` | 2 | redirect_outside_allowlist:1, access_controlled:1 | 101 | 0 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tre_sp_temas` | 3 | access_controlled:3 | 0 | 0 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `trf2_eproc_jurisprudencia` | 2 | access_controlled:2 | 217 | 4 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `trf4_eproc_jurisprudencia` | 2 | redirect_outside_allowlist:1, access_controlled:1 | 106 | 0 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `trf5_jurisprudencia` | 3 | candidate:1, valid:2 | 13 | 47 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `trf6_eproc_jurisprudencia` | 2 | access_controlled:2 | 224 | 4 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tst_jurisprudencia` | 5 | robots_disallowed:5 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |

## Interpretação

Este artefato é evidência de discovery, não promoção automática de parser.
POSTs não foram submetidos sem payload contratado. Bloqueios, robots, SSO, rate limit, timeout e indisponibilidade permanecem estados explícitos.

O JSON contém hashes, rotas, filtros, comparação de contrato e TODOs por provider.

## Candidates do catálogo sem adapter runtime

| Source | Status live | Observações | Próximo passo |
| --- | --- | ---: | --- |
| `falcao_jt` | observed | 1 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `justica_eleitoral_sjur` | observed | 5 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `tjap_tucujuris` | observed | 5 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `tjes_jurisprudencia` | observed | 1 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `tjmg_jurisprudencia` | observed | 5 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `tjrn_jurisprudencia` | observed | 5 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `tjse_jurisprudencia` | observed | 1 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `trf3_jurisprudencia` | observed | 5 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
| `trt2_pje_jurisprudencia` | observed | 1 | criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico |
