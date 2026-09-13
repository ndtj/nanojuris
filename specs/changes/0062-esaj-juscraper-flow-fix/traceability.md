# Rastreabilidade

| Requisito | Implementação | Teste/Evidência |
|---|---|---|
| REQ-001/002 | `fetch_cjsg_page`, `TjspCjsgProvider.search` | testes eSAJ de página 1 |
| REQ-003 | fluxo de página 1 + página N | testes de paginação |
| REQ-004 | extração/propagação de `conversationId` TJSP | `test_tjsp_cjsg.py` |
| REQ-005 | diagnósticos existentes e fixtures negativas | testes de acesso/contrato |
| REQ-006 | métodos e modelos públicos inalterados | suíte de providers |
| REQ-007/008 | fixtures sintéticas e sem deploy | auditoria/gates |
