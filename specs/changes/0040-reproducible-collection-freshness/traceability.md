# Rastreabilidade — coleta e freshness

| Requisito | Critério | Tarefa | Evidência | Estado |
| --- | --- | --- | --- | --- |
| REQ-001, REQ-002 | AC-004 | T01–T03 | checkpoint v2 com fingerprints e roundtrip | pass |
| REQ-003, REQ-004 | AC-001, AC-002, AC-003 | T03, T04 | restart, deduplicação e incompatibilidade | pass |
| REQ-005 | AC-003, AC-006 | T02, T04 | freshness por relatório, sem inferência | pass |
| REQ-009 | AC-004 | T07 | manifesto no relatório/store e export Markdown/JSON | pass |
| REQ-008, REQ-010 | AC-005, AC-006 | T06, T08 | limites de execução, crash/restart, drift, duplicidade, disco cheio e benchmark | pass |
| REQ-006 | AC-003 | T05 | ledger opt-in de tombstone com URL HTTPS, hash, tipo e motivo; sem remoção implícita | pass |
| REQ-007 | AC-005 | T05 | raw efêmero por padrão, store sem purge automático e cache com limpeza opt-in limitada | pass |
