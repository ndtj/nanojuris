# SDD 0099 — Meta de busca: rotas federais TRF1/TRF2/TRF4

Status: `proposed`

Esta meta inicia a próxima onda de descoberta de fontes, sem alterar a
federação padrão. O objetivo é localizar e provar, por chamadas públicas
bounded, a melhor rota oficial de jurisprudência textual de segundo grau para
TRF1, TRF2 e TRF4.

## Por que esta é a próxima meta

- o inventário nacional registra lacunas ou validação incompleta nessas três
  superfícies;
- federal é uma família independente dos portais estaduais e pode reutilizar
  contratos de inteiro teor e paginação já existentes;
- uma chamada oficial bem-sucedida permite implementar adapters em um lote
  pequeno, reduzindo risco e custo de investigação;
- bloqueios de acesso continuam evidência de bloqueio, nunca resultado vazio.

## Artefatos

- `spec.md`: escopo e critérios de aceite;
- `design.md`: protocolo de busca pública e classificação;
- `tasks.md`: tarefas T001–T012 desta meta;
- `GOAL_EXECUTOR_PROMPT.md`: instrução autocontida para execução;
- `verification.md`: registro de chamadas, evidências e decisão.

Esta meta não autoriza bypass, credenciais, commit, push, deploy ou alteração
de produção.
