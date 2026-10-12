# Sweep live de todos os providers

Gerado em `2026-10-12T17:10:01+00:00`; modo `live_bounded`; providers: **26**.

## Resumo

- Observados: **26**; sem observação: **0**.
- Rotas declaradas: **87**; candidatas observadas: **2147**.
- Filtros declarados: **172**; campos observados: **201**.
- Providers com sinais de controle de acesso: **5**.

## Matriz de maturação da evidência

| Provider | Observações | Status | Rotas | Filtros | TODO principal |
| --- | ---: | --- | ---: | ---: | --- |
| `tjac_cjsg` | 2 | valid:1, empty:1 | 68 | 5 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjal_cjsg` | 2 | valid:1, empty:1 | 76 | 4 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjam_cjsg` | 2 | robots_disallowed:2 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjba_graphql` | 2 | empty:2 | 0 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjce_cjsg` | 2 | robots_disallowed:2 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjce_informativos` | 2 | valid:1, empty:1 | 370 | 16 | nenhum TODO automático |
| `tjce_sjuris` | 2 | valid:2 | 11 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjdf_juris` | 2 | candidate:2 | 34 | 0 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjgo_projudi_jurisprudencia` | 2 | access_controlled:1, valid:1 | 96 | 6 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjma_jurisconsult` | 2 | candidate:1, empty:1 | 7 | 0 | capturar e validar GETs declarados ainda não observados |
| `tjms_cjsg` | 2 | valid:1, empty:1 | 99 | 5 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjmt_jurisprudencia_api` | 2 | candidate:2 | 35 | 0 | capturar e validar GETs declarados ainda não observados |
| `tjpa_jurisprudencia_bff` | 2 | valid:2 | 6 | 1 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjpb_pje_jurisprudencia` | 2 | valid:2 | 17 | 10 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjpe_jurisprudencia` | 2 | robots_disallowed:2 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjpi_juspi` | 2 | candidate:1, valid:1 | 6 | 7 | capturar e validar GETs declarados ainda não observados |
| `tjpr_jurisprudencia` | 2 | empty:1, valid:1 | 203 | 49 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjrj_eproc_jurisprudencia` | 2 | redirect_outside_allowlist:1, access_controlled:1 | 108 | 0 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjro_liame` | 2 | access_controlled:1, empty:1 | 32 | 5 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjrr_juris` | 2 | valid:2 | 32 | 18 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjrs_solr` | 2 | valid:1, robots_disallowed:1 | 427 | 68 | revisar robots.txt e agendar nova coleta autorizada |
| `tjsc_eproc_jurisprudencia` | 2 | source_unavailable:1, access_controlled:1 | 117 | 0 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjsp_cjsg` | 2 | valid:1, empty:1 | 98 | 7 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjsp_eproc_jurisprudencia` | 2 | redirect_outside_allowlist:1, valid:1 | 87 | 0 | documentar controle de acesso/SSO e confirmar rota pública alternativa |
| `tjsp_nugepnac` | 2 | valid:1, candidate:1 | 218 | 0 | capturar e validar GETs declarados ainda não observados |
| `tjto_jurisprudencia` | 2 | robots_disallowed:2 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |

## Interpretação

Este artefato é evidência de discovery, não promoção automática de parser.
POSTs não foram submetidos sem payload contratado. Bloqueios, robots, SSO, rate limit, timeout e indisponibilidade permanecem estados explícitos.

O JSON contém hashes, rotas, filtros, comparação de contrato e TODOs por provider.
