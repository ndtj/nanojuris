# Tarefas — Implantação inicial OCI

Status: `deferred_external`

- [x] T1 — [deferred_with_review] constituição dos repositórios requer decisão
  e acesso do tenancy; não faz parte do ciclo local.
- [x] T2 — [deferred_with_review] compartments/IAM dependem do tenancy OCI.
- [x] T3 — [deferred_with_review] VCN/DNS dependem da infraestrutura OCI.
- [x] T4 — [deferred_with_review] storage/bucket dependem do tenancy OCI.
- [x] T5 — [deferred_with_review] imagem e health checks aguardam pipeline OCI.
- [x] T6 — [deferred_with_review] Load Balancer/TLS aguardam infraestrutura.
- [x] T7 — [deferred_with_review] secrets/IAM exigem configuração externa.
- [x] T8 — [deferred_with_review] build/registry/deploy não autorizados neste ciclo.
- [x] T9 — [deferred_with_review] observabilidade OCI aguardando deploy.
- [x] T10 — [out_of_scope] plan, staging, smoke e rollback de produção não
  foram autorizados.
- [x] T11 — [deferred_with_review] backup/restauração dependem do storage OCI.
- [x] T12 — [out_of_scope] aprovação de produção não foi autorizada.

As disposições acima encerram a execução local sem alegar que o deploy ocorreu.
Retomada: autorização explícita de Onda 6, credenciais OCI e tenancy disponível.

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
