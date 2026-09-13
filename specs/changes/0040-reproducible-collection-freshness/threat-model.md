# Threat model — coleta reprodutível

| Ameaça | Impacto | Controle |
| --- | --- | --- |
| tráfego ou disco ilimitado | alto | budgets e limites obrigatórios |
| checkpoint avança sem dados | alto | transação atômica |
| replay duplica registros | alto | idempotency key e identidade 0037 |
| raw/cache expõe PII | alto | opt-in, redaction, retenção e cleanup |
| ausência vira exclusão falsa | alto | tombstone somente com prova |
| manifest contém segredo | crítico | allowlist de campos e redaction |
