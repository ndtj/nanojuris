# Fila da proxima onda de adapters (2026-09-01)

Quadro offline de prontidao. Ele nao chama fontes, nao copia Juscraper e nao promove providers.

- Commit upstream: `604c1dd70d6f313011cc1079790febe6c71807e2`
- Itens: **8**
- Estados: `{"blocked_access": 2, "candidate_ready_for_contract_closure": 1, "covered_requires_differential_fixture": 1, "detail_contract_unverified": 1, "separate_collection_contract": 3}`

| Onda | Source ID | Superficie | Prioridade | Evidencia live mais recente | Estado | Proxima trava |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | `tjes_jurisprudencia` | `cjsg` | P0 | `reachable_valid_data` (recheck:http_200) | `candidate_ready_for_contract_closure` | fechar reuso, fixtures e limites; nao promover ainda |
| A2 | `tjrn_jurisprudencia` | `cjsg` | P0 | `blocked_access` (recheck:http_403) | `blocked_access` | replay publico sem bloqueio e evidencias negativas antes de parser |
| A3 | `tjro_jurisprudencia` | `cjsg` | P1 | `reachable_empty_data` (dedicated:http_200) | `covered_requires_differential_fixture` | capturar fixture propria e executar comparacao diferencial |
| A4 | `tjto_ementa_detail` | `detail` | P1 | `not_recorded` (none) | `detail_contract_unverified` | reproduzir detalhe lazy, pareamento e falhas parciais |
| C1 | `tjes_cjpg` | `cjpg` | P2 | `reachable_valid_data` (dedicated:http_200) | `separate_collection_contract` | revisar reuso e manter opt-in; nao misturar com CJSG ou processo |
| C2 | `tjes_turma_recursal` | `cjpg` | P2 | `not_recorded` (none) | `separate_collection_contract` | abrir contrato da collection sem misturar CJSG/processo |
| C3 | `tjsp_cjpg` | `cjpg` | P2 | `reachable_valid_data` (dedicated:http_200) | `separate_collection_contract` | abrir contrato da collection sem misturar CJSG/processo |
| C4 | `tjto_cjpg` | `cjpg` | P2 | `blocked_access` (dedicated:http_403) | `blocked_access` | replay publico sem bloqueio e evidencias negativas antes de parser |

## Regras de retomada

- **A1 / tjes_jurisprudencia**: reuso aprovado, fixtures proprias e contrato de paginacao fechado.
- **A2 / tjrn_jurisprudencia**: rota publica voltar a responder sem bloqueio de acesso.
- **A3 / tjro_jurisprudencia**: rota geral oficial, filtros e contrato forem reproduzidos.
- **A4 / tjto_ementa_detail**: rota de detalhe e pareamento com listagem forem comprovados.
- **C1 / tjes_cjpg**: revisao de reuso aprovar a coleta e o contrato continuar estavel.
- **C2 / tjes_turma_recursal**: binding de turma recursal e semantica propria forem confirmados.
- **C3 / tjsp_cjpg**: rota CJPG oficial e contrato independente forem confirmados.
- **C4 / tjto_cjpg**: rota CJPG oficial e separacao de grau forem confirmadas.

## Limites

- A classificacao combina evidencia estatica e fotografias live bounded; nao fecha contrato.
- Nenhum corpo de resposta foi promovido a fixture ou federacao padrao.
- Reuso, equivalencia, identidade e seguranca continuam gates por pacote.
