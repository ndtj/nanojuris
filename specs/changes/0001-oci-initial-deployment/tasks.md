# Tarefas — Implantação inicial OCI

Status: `proposed`

- [ ] T1 — aprovar constituição dos dois repositórios
- [ ] T2 — criar compartments e políticas IAM mínimas
- [ ] T3 — criar VCN, subnets, NSGs e DNS
- [ ] T4 — criar storage persistente e bucket privado de backup
- [ ] T5 — criar imagem de execução e health/readiness checks
- [ ] T6 — criar Load Balancer e TLS
- [ ] T7 — configurar secrets e identidades sem chaves no Git
- [ ] T8 — configurar build, registry e deploy
- [ ] T9 — configurar logs, métricas, alertas e auditoria
- [ ] T10 — executar plan, staging, smoke test e rollback
- [ ] T11 — testar backup e restauração
- [ ] T12 — aprovar produção e registrar evidência

## Rastreabilidade de execucao

- T1/T2/T3: `REQ-001`, `REQ-003`;
- T4/T11: `REQ-004`;
- T5/T6: `REQ-002`;
- T7/T8: `REQ-003`, `REQ-004`;
- T9/T10: `REQ-005`, `REQ-006`;
- T12: `AC-009`, `REQ-004`.

Cada tarefa deve atualizar a matriz de `traceability.md` e registrar comando,
resultado ou impedimento antes de ser marcada como concluida.

## Ordem

```text
T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9 → T10 → T11 → T12
```
