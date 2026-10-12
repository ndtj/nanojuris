# Traceability

| Requisito | Implementacao/evidencia | Verificacao |
| --- | --- | --- |
| REQ-001 | `_initialize_public_access_session` antes do POST principal | teste de ordem de chamadas |
| REQ-002 | substituicao de `payload["uuidCaptcha"]` | teste de payload |
| REQ-003 | fallback para payload original e diagnostico posterior | teste de controle |
| REQ-004 | `AccessControlRequiredError` e estados existentes | suite TJSP |
| REQ-005 | README, source contract e exemplo atualizados | auditoria documental |
