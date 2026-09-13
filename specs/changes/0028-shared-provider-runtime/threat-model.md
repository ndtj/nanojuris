# Threat model — runtime compartilhado

Status: pending

| ID | Ameaça | Impacto | Controle |
| --- | --- | --- | --- |
| TH-001 | SSRF e redirect externo | alto | allowlist e validação por salto |
| TH-002 | segredo em log | alto | redaction estrutural e testes |
| TH-003 | retry storm | alto | budget, jitter e circuit breaker |
| TH-004 | cache cross-provider | alto | namespace e chave completa |
| TH-005 | resposta excessiva | alto | limite streaming |
| TH-006 | TLS inseguro | alto | verificação obrigatória |
| TH-007 | defaults agressivos | médio | configuração conservadora e review |

Risco residual: indisponibilidade externa não pode ser eliminada; deve ser
isolada e diagnosticada.
