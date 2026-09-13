# Threat model

| ID | Risco | Mitigação |
|---|---|---|
| TH-001 | PDF fora do host oficial | allowlist de hostname, HTTPS e path |
| TH-002 | arquivo malformado ou grande | limite de bytes/páginas e validação `%PDF-` |
| TH-003 | bloqueio confundido com vazio | estados explícitos no trace |
| TH-004 | coleção curada apresentada como cobertura integral | `total_known=false`, estado parcial e limitações explícitas |
| TH-005 | excesso de requisições | rate limit compartilhado e uma busca por fonte |
