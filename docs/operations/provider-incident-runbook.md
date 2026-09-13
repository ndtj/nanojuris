# Runbook de incidentes de providers

Este runbook orienta probes e triagem sem transformar falhas de fonte em “zero
resultados”. As ações são bounded, allowlisted e não alteram produção.

## Classificação

| Sintoma | Estado | Ação segura |
| --- | --- | --- |
| HTTP 401/403, CAPTCHA ou WAF | `blocked_access` | registrar metadados, parar e solicitar revisão/contato oficial |
| TLS, DNS, timeout ou 5xx | `blocked_transport`/`source_unavailable` | respeitar circuit breaker, aguardar janela e revalidar uma vez |
| HTTP 429 | `rate_limited` | obedecer `Retry-After`; não aumentar frequência |
| JSON/HTML sem campos contratuais | `schema_changed` | conservar fixture sanitizada, abrir revisão de parser e não retornar vazio |
| `total=0` e coleção vazia válida | `empty` | aceitar vazio somente com contrato e trace completos |

## Probe controlado

1. Confirmar host e rota na allowlist e usar termo jurídico genérico.
2. Limitar a uma chamada por superfície, página pequena e timeout global.
3. Não usar credenciais, cookies, CAPTCHA, bypass de WAF ou rota privada.
4. Persistir somente status, tamanho, hash, latência e erro redigido.
5. Comparar com a última evidência; não substituir a evidência histórica.
6. Abrir mudança SDD para qualquer alteração de contrato ou promoção.

## Alertas recomendados

- taxa de `schema_changed` ou `blocked_transport` acima do baseline por duas
  janelas consecutivas;
- p95 de latência acima do orçamento da fonte;
- queda de registros válidos acompanhada de mudança de `content_sha256`;
- aumento de `empty` sem confirmação de `total=0`.

Alertas são sinais para revisão, não autorização para retentar em massa.
