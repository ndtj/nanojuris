# Rastreabilidade — 0065

| Requisito | Implementação | Verificação |
|---|---|---|
| REQ-001 | `models.py` (`SearchPage`, estados e total explícito) | `test_data_quality_completion.py` |
| REQ-002 | `client.py`, `providers/base.py`, `collection.py` | testes de paginação e coleta |
| REQ-003 | `models.py`, `canonical.py`, CLI e MCP | `test_data_quality_completion.py`, `test_cli.py`, `test_mcp_tools.py` |
| REQ-004 | `store.py` (migração idempotente, índices e FTS5) | `test_store.py`, `test_data_quality_completion.py` |
| REQ-005 | `contracts.py`, `federated.py`, `health.py`, `validation.py` | `test_provider_contract_v2.py`, `test_health.py` |
| REQ-006 | processo local, sem comandos de publicação | revisão final e status de ondas |

As evidências live existentes permanecem separadas da verificação de contrato
local; nenhum provider foi promovido apenas por passar testes unitários.
