# Plano de tarefas

Referência: `specs/changes/NNNN-nome-curto/spec.md`

Cada tarefa deve ser pequena, verificável e indicar sua dependência.

## Tarefas

- [ ] T1 — atualizar especificação e contratos
- [ ] T2 — implementar comportamento principal
- [ ] T3 — implementar falhas e limites
- [ ] T4 — adicionar ou atualizar fixtures e testes
- [ ] T5 — atualizar documentação derivada
- [ ] T6 — executar validação completa

## Dependências

```text
T1 → T2 → T3 → T4 → T5 → T6
```

## Critério de parada

Não marcar a mudança como concluída sem evidência em `verification.md`.
