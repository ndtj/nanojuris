# Sweep live de todos os providers

Gerado em `2026-10-12T17:23:53+00:00`; modo `live_bounded`; providers: **6**.

## Resumo

- Observados: **6**; sem observação: **0**.
- Rotas declaradas: **26**; candidatas observadas: **401**.
- Filtros declarados: **45**; campos observados: **161**.
- Providers com sinais de controle de acesso: **0**.

## Matriz de maturação da evidência

| Provider | Observações | Status | Rotas | Filtros | TODO principal |
| --- | ---: | --- | ---: | ---: | --- |
| `tjac_cjsg` | 2 | valid:2 | 83 | 39 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjal_cjsg` | 2 | valid:2 | 91 | 37 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjam_cjsg` | 2 | robots_disallowed:2 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjce_cjsg` | 2 | robots_disallowed:2 | 0 | 0 | revisar robots.txt e agendar nova coleta autorizada |
| `tjms_cjsg` | 2 | valid:2 | 114 | 39 | confirmar payload, filtros e paginação dos endpoints POST com fixture |
| `tjsp_cjsg` | 2 | valid:2 | 113 | 46 | confirmar payload, filtros e paginação dos endpoints POST com fixture |

## Interpretação

Este artefato é evidência de discovery, não promoção automática de parser.
POSTs não foram submetidos sem payload contratado. Bloqueios, robots, SSO, rate limit, timeout e indisponibilidade permanecem estados explícitos.

O JSON contém hashes, rotas, filtros, comparação de contrato e TODOs por provider.
