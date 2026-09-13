# Tarefas

- [x] T01 — mapear código duplicado de transporte.
- [x] T02 — definir política, resposta imutável e taxonomia de retry.
- [x] T03 — implementar cliente seguro e redaction.
- [x] T04 — implementar budget, backoff, cache e circuit breaker.
- [x] T05 — migrar uma família e um provider independente.
- [x] T06 — testar falhas, isolamento, determinismo e compatibilidade.
- [x] T07 — documentar configuração e runbook.
- [x] T08 — executar gates e benchmark local.

Escopo desta rodada: a família TJES/TJTO e o adapter TJRN foram migrados para
`nanojuris.transport`. A migração dos demais providers permanece incremental
e é acompanhada por seus próprios contratos e fixtures.

Dependência: T01 -> T02 -> T03 -> T04 -> T05 -> T06 -> T07 -> T08.
