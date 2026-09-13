# Rastreabilidade - contrato v2

| Requisito | Criterio | Tarefa | Evidencia | Estado |
| --- | --- | --- | --- | --- |
| REQ-001 | AC-001, AC-003 | T02, T03 | schema v2, matriz e `ProviderCapabilities` | pass |
| REQ-002 | AC-003 | T02, T06 | `FilterSupport` e `test_provider_contract_v2.py` | pass |
| REQ-003 | AC-001, AC-003 | T03, T06 | metadados de `SearchPage` e testes de cursor | pass |
| REQ-004 | AC-002 | T03, T06 | `ProviderOutcome` e teste de redacao segura | pass |
| REQ-005 | AC-001 | T03, T05, T06 | modelos canonicos, fixtures BNP/STJ com ids nativos e testes de canonicalizacao | pass |
| REQ-006 | AC-004, AC-005 | T04, T05, T07 | adapter, capabilities v2 aditivas nos dois providers e docs | pass |

`pass` nesta tabela significa implementacao/teste local do contrato, nao que
todos os providers ja adotaram a versao 2.
