# Clarificações e decisões necessárias

## Decisões já fechadas pelo produto

- O objetivo é jurisprudência pública; dados processuais pertencem ao NanoJud.
- Não haverá bypass de CAPTCHA, WAF, Turnstile, login, rate limit ou TLS.
- Não haverá índice documental próprio, embeddings ou LLM por consulta.
- Cache de respostas live é permitido somente de forma efêmera e não pesquisável.
- “Todos os tribunais” é um modo explícito; o padrão pode ser adaptativo.
- Nenhuma alteração de produção, publicação ou deploy está autorizada neste
  pacote.

## Perguntas que exigem decisão humana

1. Qual responsável técnico por cada família de providers?
2. Qual política de retenção para PDFs e texto extraído por fonte?
3. Quais termos de uso permitem armazenamento temporário ou republicação?
4. Quais critérios de priorização definem a próxima leva de 1–3 tribunais?
5. Qual nível de disponibilidade live é necessário antes do rollout padrão?
6. O documento completo pode ser mostrado ao usuário ou apenas linkado?
7. Qual orçamento de latência e chamadas vale para cada ambiente?

Enquanto essas respostas não existirem, o executor pode implementar e testar
contratos, mas não deve declarar aprovação legal, retenção ou release.

## Ambiguidades que não devem ser resolvidas silenciosamente

- “Cobertura nacional” pode significar presença de fonte, consulta, ementa ou
  inteiro teor; a matriz registra cada dimensão separadamente.
- “Provider funcionando” pode significar HTTP 200, parser, resultado textual ou
  federação; apenas os gates definem promoção.
- “Contornar bloqueio” pode sugerir evasão; neste projeto significa somente
  superfície oficial alternativa ou autorização formal.

