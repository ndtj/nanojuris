# Handoff para o executor

## Ponto de entrada

Use `GOAT_EXECUTOR_PROMPT.md` como prompt principal. Ele deve ser fornecido ao
modelo executor junto com acesso aos dois repositórios locais.

## Estado entregue

- Planejamento/SDD: concluído.
- Implementação funcional: não iniciada por solicitação do usuário.
- Tarefas concluídas: T01–T03.
- Próxima tarefa: T04, baseline reproduzível antes de editar código.
- Produção: intocada.
- Git: nenhum commit, push ou tag criado por este pacote.

## Ordem de leitura curta

1. `GOAT_EXECUTOR_PROMPT.md`.
2. `spec.md`.
3. `design.md` e `api-contract.md`.
4. `tasks.md` e `traceability.md`.
5. `benchmark-plan.md` e `verification.md`.
6. ADRs, threat model, research e clarify para decisões/riscos.

## Decisões que não devem ser reabertas

- sem índice próprio;
- sem IA/embedding/reranker por consulta;
- adaptive 8–12 fontes como alvo default;
- score absoluto independente da onda;
- ranking query-specific em sidecar, não em registros canônicos;
- endpoint de plano sem chamadas externas;
- ondas sequenciais no browser para respeitar guardrails;
- atualização contínua antes do freeze e manual depois;
- telemetria mínima desligada sem secret;
- nenhum deploy sem nova autorização.

## Critério para aceitar o trabalho do executor

Não aceitar apenas “testes verdes”. Conferir AC-001–AC-024, métricas do holdout,
performance, logs/redaction, equivalência entre ondas, compatibilidade legada e
confirmação explícita de ausência de commit/push/deploy.
