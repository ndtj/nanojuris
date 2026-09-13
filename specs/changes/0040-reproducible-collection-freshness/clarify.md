# Clarificação — coleta e freshness

Status: resolved_for_design

| ID | Pergunta | Decisão | Estado |
| --- | --- | --- | --- |
| Q-001 | objetivo é espelhar todo o Brasil? | não | resolved |
| Q-002 | bytes brutos são obrigatórios? | não; manifest/hash obrigatório, bytes opt-in | resolved |
| Q-003 | retomada cruza versão de parser? | somente com compatibilidade explícita | resolved |
| Q-004 | ausência na próxima coleta é tombstone? | não sem prova da fonte | resolved |
| Q-005 | coleta ilimitada pode ser default? | não | resolved |
| Q-006 | backend servidor entra? | pacote próprio futuro | resolved |
| Q-007 | qual retenção default de raw/store? | raw bytes efêmeros; store canônico sem purge automático; cache somente com cleanup opt-in e limites explícitos | resolved |
