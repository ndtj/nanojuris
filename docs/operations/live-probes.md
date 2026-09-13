# Probes live bounded

`run_allowlisted_probe(client, ProbePolicy(...))` é a única superfície
recomendada para validar contratos live em lote pequeno. A política exige uma
lista de providers, texto jurídico genérico, `page_size` baixo e timeout
global. O retorno contém somente metadados, hashes, status e latências.

Os SLIs são ponto no tempo: taxa de contrato aprovado, contagem por status e
latências P50/P95. Eles não representam disponibilidade permanente. HTTP 403,
429, TLS, timeout, WAF e mudança de schema permanecem estados distintos e
devem ser triados em [provider-incident-runbook.md](provider-incident-runbook.md).
