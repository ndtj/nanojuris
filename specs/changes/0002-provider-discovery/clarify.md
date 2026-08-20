# Perguntas e decisões de esclarecimento

Referência: `specs/changes/0002-provider-discovery/spec.md`

## Decisões resolvidas

| ID | Pergunta | Decisão | Motivo |
| --- | --- | --- | --- |
| Q-001 | A biblioteca externa será obrigatória? | Não. | Descoberta não pode comprometer o runtime principal. |
| Q-002 | A descoberta pode acessar fontes públicas? | Sim, somente em execução explicitamente iniciada e bounded. | Preserva utilidade sem criar crawler ilimitado. |
| Q-003 | A descoberta pode promover provider automaticamente? | Não. | Promoção exige contrato, fixtures, testes e aceite humano. |
| Q-004 | Como tratar bloqueio? | Estado explícito, nunca vazio. | Regra constitucional do NanoJuris. |
| Q-005 | O navegador pode usar stealth, proxy, cookies ou solver? | Não no fluxo NanoJuris. | Não fazem parte da descoberta legítima de fonte pública. |

## Questões abertas

- `O-001`: definir, em mudança futura, a política de retenção de corpos brutos
  capturados fora dos fixtures minimizados.
- `O-002`: definir se o Studio exibirá evidências de descoberta ou apenas os
  artefatos SDD exportados.
- `O-003`: decidir se a execução dinâmica será ativada no CI ou somente por
  operador local.
