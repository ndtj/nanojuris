# Pesquisa

A auditoria offline encontrou um campo `invalid_records` retornado como zero
mesmo quando a canonicalização abortava o lote, e uma chave global baseada
apenas em número de processo no cliente. A busca agregada já preserva erros e
fontes ignoradas, mas precisa de invariantes explícitos para evitar divergência
entre adaptadores e runtime.

Evidências de baseline: `771 passed, 8 skipped` com `PYTHONPATH=.`; auditorias
de providers e contrato executadas antes desta mudança.
