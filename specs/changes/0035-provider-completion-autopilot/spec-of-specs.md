# Spec-of-specs — conclusão contínua dos providers

Status: proposed

## Papel

Este pacote é a camada operacional do programa 0026. Ele não substitui os
pacotes 0027–0034 nem os SDDs individuais: mantém inventário, work packs, estado,
prioridade e checkpoints para que outra IA ou pessoa retome o trabalho sem
depender do histórico da conversa.

## Unidades

- provider-baseline.json: fotografia gerada e imutável da auditoria local;
- execution-state.json: estado retomável por provider;
- provider-workpacks/: contrato de conclusão individual;
- provider-completion-summary.md: fila legível;
- AUTONOMOUS_EXECUTION.md: protocolo central de execução;
- verification.md: evidência do gerador e do estado.

## Condição terminal

Uma `coverage_epoch` termina quando cada unidade elegível estiver `accepted`,
`accepted_with_limitations`, `rejected`, `deferred_with_review` ou
`out_of_scope`, com evidência e justificativa. Bloqueio externo é estado de
saúde/espera; não encerra sozinho o trabalho seguro disponível.
