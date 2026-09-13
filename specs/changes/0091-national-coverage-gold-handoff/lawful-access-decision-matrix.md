# Matriz de acesso público legítimo

Use esta matriz antes de qualquer chamada. Ela complementa o playbook em
`docs/coverage/public-access-boundary-playbook-20260908.md`.

| Situação observada | Ação permitida | Estado | Próxima ação |
| --- | --- | --- | --- |
| GET/POST público documentado | executar bounded, rate-aware | `success`/`empty` | validar contrato |
| redirect oficial | seguir poucos redirects | `success` | registrar URL final |
| cookie/CSRF emitido no fluxo público | usar só na sessão efêmera | `success` | não persistir segredo |
| export/API/RSS/sitemap oficial | preferir ao scraping HTML | `success` | validar licença/limite |
| paginação publicada | respeitar cursor/limite | `partial` ou `success` | não aumentar janela sem prova |
| desafio aparece mas fluxo prossegue sem solver | seguir somente a página permitida | `challenge_incidental` | registrar limitação |
| desafio exige clique/solução humana | parar automação | `challenge_enforced` | pedir ação humana/allowlist |
| 403/429/WAF/Turnstile | não repetir contra a proteção | `access_blocked`/`rate_limited` | procurar alternativa oficial |
| login ou autorização | não automatizar sem autorização explícita | `access_blocked` | solicitar API/conta institucional |
| TLS/reset/timeout persistente | retry transitório limitado; depois parar | `transport_error` | abrir chamado ou registrar blocker |
| schema inesperado | preservar resposta redigida e parar parser | `schema_invalid` | atualizar contrato após investigação |
| documento fora do host allowlist | não baixar | `document_blocked` | validar rota oficial |

## Nunca permitido

CAPTCHA/Turnstile solver ou OCR, bypass de WAF, stealth, spoofing de navegador,
rotação de IP/proxy para ocultar automação, replay de token/cookie, TLS
desativado, fuzzing de endpoint privado, tentativa de autenticação indevida,
exaurir rate limit, alterar cabeçalhos para fingir outro cliente ou “explorar a
zona de sombra”.

## Evidência mínima de bloqueio

```text
source_id, url, método, data/hora, status HTTP ou fingerprint redigido,
etapa do fluxo, classificação, alternativa oficial consultada,
ação externa necessária, TTL para rechecagem
```
