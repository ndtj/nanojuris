# Rastreabilidade

| Requisito | Implementação | Evidência |
|---|---|---|
| REQ-001 | `TjceTlsAdapter` | testes de montagem/verify |
| REQ-002/003 | transporte JSF TJPE | testes de sequência e parser |
| REQ-004 | retry bounded por provider | testes de 429/5xx/timeout |
| REQ-005 | `SourceTrace` + `raw` | testes de hashes e fallback |
| REQ-006 | construtores e IDs legados | suíte de providers |
| REQ-007/008 | fixtures sanitizadas e limites | auditoria SDD/gates |
