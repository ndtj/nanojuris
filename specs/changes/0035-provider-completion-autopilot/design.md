# Design — orquestração retomável

## Modelo de estado

Estados de trabalho:

    not_started -> active -> waiting_evidence -> ready_for_review
         ^             |              |              |
         |             +-----------> stale <---------+
         |                                            |
         +--------------------------------------------+

Disposições terminais, sempre justificadas:

- `accepted`;
- `accepted_with_limitations`;
- `rejected`;
- `deferred_with_review`;
- `out_of_scope`.

`blocked` não é estado terminal. Um controle externo pode impedir a validação
live e ainda deixar disponíveis tarefas offline de contrato, fixture, parser,
documentação, threat model ou pesquisa.

## Eixos independentes

Cada item mantém separadamente:

- `status`: avanço do trabalho;
- `phase`: inspect, research, clarify, specify, design, implement, verify ou review;
- `operational_health`: not_checked, valid, empty_confirmed, degraded,
  rate_limited, access_controlled, tls_error, schema_changed, unavailable ou unknown;
- `disposition`: decisão de programa quando terminal;
- `evidence_fingerprint`: hash dos fatos que sustentam prioridade e conclusão;
- `review_after` e `resume_when`: retomada objetiva de deferimentos.

## Seleção

1. executar 0036 para criar o universo nacional por coleção;
2. fechar 0037 e 0038 como gates de identidade e federação;
3. selecionar o menor `priority` entre itens não terminais e não dependentes;
4. dentro da prioridade, favorecer maior lacuna de cobertura e maior risco;
5. limitar cada ciclo a uma unidade revisável: fundação, coleção ou superfície.

O catálogo atual alimenta a fila de providers existentes. Candidatos externos
entram primeiro no ledger 0029/0039 e só recebem `source_id` runtime após intake
e contrato aprovados.

## Checkpoint e regeneração

Após cada tarefa:

- atualizar `execution-state.json`;
- registrar comando, evidência e outcome;
- manter work pack e SDD coerentes;
- executar teste focado;
- não acumular mudanças não relacionadas.

O gerador recalcula o fingerprint a partir de lifecycle, role, maturidade, alvo,
prioridade e lacunas. Se ele mudar após uma disposição terminal, o item volta a
`stale`/`inspect`; evidência histórica não é apagada.

## Deferimento controlado

Após três ocorrências equivalentes sem nova evidência, registrar o diagnóstico
e avançar na fila. `deferred_with_review` só é válido com:

- causa comprovada;
- tarefas seguras restantes esgotadas;
- owner;
- `review_after` ou evento de revisão;
- `resume_when` testável;
- impacto explícito na cobertura.

## Isolamento

Falha de um provider não bloqueia a fila inteira. Problemas compartilhados abrem
pacote de família; lacunas transversais voltam para 0027, 0028, 0031, 0037,
0038 ou 0040, evitando correções divergentes por adapter.
