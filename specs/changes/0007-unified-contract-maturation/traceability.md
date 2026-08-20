# Traceability

| Requisito | Implementação/evidência | Validação |
|---|---|---|
| RF-001 | `tools/audit_unified_contract.py`, `unified-contract-matrix.json` | `tests/test_unified_contract_audit.py` |
| RF-002 | `ProviderCapabilities.supported_filters`, matriz de cobertura | teste de contagem e lacunas |
| RF-003 | perfis semânticos derivados de categoria/canônicos | teste de perfis |
| RF-004 | `SearchPage`, `source_completeness`, `completeness_reason` | testes de client/routing existentes |
| RF-005 | discovery e política SDD | `tests/test_all_provider_discovery.py` |
| RF-006 | `gaps` por provider e TODOs do sweep | matriz JSON/Markdown |
| RF-007 | classificação de erros e access status | smoke live versionado |
| RF-008 | ferramenta sem rede por padrão | teste offline |
