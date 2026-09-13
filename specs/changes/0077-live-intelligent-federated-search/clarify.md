# Clarificação — busca live inteligente

Mudança: `specs/changes/0077-live-intelligent-federated-search/spec.md`
Responsável por responder: Product Owner NanoJuris
Status: `resolved`

## Decisões fechadas

| ID | Pergunta | Resposta aprovada | Consequência | Status |
| --- | --- | --- | --- | --- |
| Q-001 | Haverá índice documental próprio? | Não. | A recuperação fica limitada às janelas retornadas pelos providers. | resolved |
| Q-002 | Haverá LLM, embedding ou reranker pago por consulta? | Não. | O ranking será determinístico e CPU-only. | resolved |
| Q-003 | Quais fontes entram por padrão? | Roteamento adaptativo de 8 a 12 fontes. | Três fontes fixas deixam de ser o único default. | resolved |
| Q-004 | Como resultados tardios aparecem? | Reordenação contínua até interação. | Depois da interação, a ordem congela e surge ação para atualizar. | resolved |
| Q-005 | O ranking será explicado? | Sim, até três razões compactas por cartão. | A API precisa retornar evidência estruturada. | resolved |
| Q-006 | “Todos os tribunais” continuará existindo? | Sim, como modo explícito. | Busca adaptativa não limita a escolha consciente do usuário. | resolved |
| Q-007 | Cache é permitido? | Sim, apenas efêmero e não pesquisável. | TTL de 5–15 minutos e chave versionada. | resolved |
| Q-008 | Qual a prioridade do produto? | Precisão do top 10. | Recall nacional continua condicionado aos providers live. | resolved |
| Q-009 | Pode haver telemetria? | Somente mínima, agregada e sem consulta em claro. | Fingerprint HMAC e retenção de 30 dias. | resolved |
| Q-010 | Pode publicar ou implantar? | Não neste ciclo. | Implementação local, feature flag e plano de rollout apenas. | resolved |

## Hipóteses que exigem medição, não decisão de produto

| ID | Hipótese | Validação | Gate |
| --- | --- | --- | --- |
| H-001 | 8–12 fontes equilibram relevância e latência. | Benchmark live com 3, 8, 10 e 12 fontes. | T48 |
| H-002 | Até 240 candidatos cabem em 150 ms p95. | Microbenchmark repetível. | T47 |
| H-003 | Uma chamada por provider oferece candidatos suficientes. | Recall@50 por query do benchmark. | T49 |
| H-004 | Regras jurídicas superam o contador atual. | Julgamento cego e nDCG@10. | T50 |
| H-005 | Ondas de 3–4 fontes produzem percepção rápida. | p50 do primeiro resultado e p95 da consolidação. | T51 |

## Regras para o executor

- Hipótese reprovada deve gerar ajuste de peso ou orçamento dentro dos limites
  desta especificação, não mudança silenciosa para índice ou IA.
- Nenhuma inferência ambígua pode se tornar filtro restritivo sem ação do
  usuário.
- O executor não precisa pedir decisões adicionais sobre arquitetura. Se um
  detalhe de implementação não estiver especificado, deve escolher a opção
  mais simples, determinística, compatível e mensurável.

## Decisão de saída

- [x] Perguntas críticas resolvidas.
- [x] Hipóteses possuem teste e gate.
- [x] Mudança pode seguir para implementação por outro modelo.
