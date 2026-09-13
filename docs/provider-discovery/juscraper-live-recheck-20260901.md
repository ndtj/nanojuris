# Rechecagem live Juscraper - 2026-09-01

Uma chamada publica por endpoint, sem credenciais e sem persistir corpo de
resposta. Este artefato e complementar ao smoke anterior e nao promove
adapters.

| Fonte | Resultado | Classificacao |
| --- | --- | --- |
| TJES `/consulta-jurisprudencia/api/search` | HTTP 200 JSON, 1 registro | `reachable_valid_data` |
| TJRN `/api/pesquisar` | HTTP 403 Access Denied | `blocked_access` |

O HTTP 403 do TJRN nesta janela e bloqueio de acesso, nao lista vazia e nao
prova ausencia de acervo. O contrato anterior de HTTP 200 continua preservado
em `juscraper-live-smoke-20260901.json` como evidencia historica. O TJES foi
posteriormente implementado como adapter opt-in no SDD `0049`; o TJRN continua
candidato ate contrato completo, fixtures e revisao de reuso.
