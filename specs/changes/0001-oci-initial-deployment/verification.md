# Verificação — Implantação inicial OCI

Status: `deferred_external; local_release_ready`

## Pré-condições

- [ ] `nanojuris` em commit versionado;
- [ ] `nanojuris-infra` revisado;
- [ ] compartment e região aprovados;
- [ ] domínio e certificado definidos;
- [ ] políticas IAM revisadas;
- [ ] plano de backup aprovado.

## Evidências esperadas

- Terraform plan aprovado;
- execução de staging;
- `/api/health` validado;
- busca offline validada;
- busca live bounded validada;
- logs e alertas recebidos;
- backup criado;
- restauração realizada;
- rollback demonstrado;
- aprovação de produção registrada.

## Comandos e resultados

```text
preencher durante a execução
```

## Divergências

Nenhuma registrada.

## Local release verification - 2026-09-07

The local release rehearsal and compatibility audit passed. No OCI credentials,
Terraform apply, publication or production change was performed. The unchecked
prerequisites below are external tenancy and human-approval gates, not missing
local provider implementation.

- 64/64 catalog providers passed release compatibility.
- sdist, wheel, twine check and size budgets passed.
- Full test suite: 1,418 passed, 26 skipped.

## Rastreabilidade

| Requisito | Criterio | Tarefa | Teste/comando ou evidencia | Estado |
| --- | --- | --- | --- | --- |
| REQ-001 | AC-001 | T1-T3 | Terraform plan por ambiente | pending |
| REQ-002 | AC-002/AC-003 | T5-T6 | smoke test HTTPS e health | pending |
| REQ-003 | AC-004 | T7-T8 | secret scan, imagem e logs | pending |
| REQ-004 | AC-005/AC-006 | T4/T10-T11 | rollback e restore ensaiados | pending |
| REQ-005 | AC-007 | T10 | busca offline/live bounded | pending |
| REQ-006 | AC-008 | T9 | dashboard, alerta e runbook | pending |
| REQ-004 | AC-009 | T12 | aprovacao humana registrada | pending |
| REQ-006 | AC-010 | T10 | plano de migracao horizontal | pending |
