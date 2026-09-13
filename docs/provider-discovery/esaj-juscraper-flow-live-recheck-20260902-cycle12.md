# Rechecagem live do fluxo eSAJ/Juscraper — ciclo 12

Em 2026-09-02 foi feita uma rodada bounded, sem credenciais e sem persistir
corpos, para confirmar o fluxo `POST resultadoCompleta.do` seguido de
`GET trocaDePagina.do` na mesma sessão.

| Provider | Resultado observado | Classificação |
| --- | --- | --- |
| TJAC/CJSG | HTTP 200, zero resultados explícitos (`Acórdãos(0)`) | `implemented` |
| TJAL/CJSG | HTTP 200, 1 registro, total 159.266 | `implemented` |
| TJAM/CJSG | HTTP 200, 1 registro, total 39.557 | `implemented` |
| TJCE/CJSG | conexão resetada pelo host remoto | `blocked_transport` |
| TJMS/CJSG | HTTP 200, 1 registro, total 230.568 | `implemented` |
| TJSP/CJSG | captcha/controle de acesso | `blocked_access` |

TJAC deixou de ser classificado como quebra de parser: a variante oficial de
zero resultados passou a ser reconhecida. TJCE e TJSP continuam bloqueios
externos e não foram contornados. Detalhes somente em
[`esaj-juscraper-flow-live-recheck-20260902-cycle12.json`](esaj-juscraper-flow-live-recheck-20260902-cycle12.json).
