# Perguntas e decisões de esclarecimento

Referência: `specs/changes/0003-premium-team-operating-model/spec.md`

## Decisões resolvidas

| ID | Pergunta | Decisão |
| --- | --- | --- |
| Q-001 | A equipe será organizada por provider ou por competências? | Por competências, com células temporárias por provider. |
| Q-002 | Um agente pode especificar, implementar e aprovar a mesma mudança? | Pode executar fases, mas não encerra sozinho a própria mudança. |
| Q-003 | A descoberta é parte do runtime do provider? | Não; é uma capacidade de pesquisa separada. |
| Q-004 | Qual é o gate de um provider premium? | Contrato confirmado, identidade estável, texto, datas, traces, fixtures, testes e operação documentada. |
| Q-005 | Quem autoriza produção? | Responsável humano operacional, com evidência registrada. |

## Questões abertas

- `O-001`: nomear formalmente os responsáveis humanos por domínio, segurança e
  operação.
- `O-002`: definir cadência de revisão de catálogo e de SLOs.
- `O-003`: definir orçamento de execução live e política de retenção de
  evidências.
- `O-004`: definir a ferramenta externa de gestão de tarefas, se necessária.
