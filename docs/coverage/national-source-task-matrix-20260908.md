# Inventário nacional de tribunais e fontes

O inventário operacional atual está no SDD 0098:

- [matriz JSON](../../specs/changes/0098-national-jurisprudence-gold-coverage/national-source-task-matrix.json)
- [resumo Markdown](../../specs/changes/0098-national-jurisprudence-gold-coverage/national-source-task-matrix.md)
- [tarefas T047–T060](../../specs/changes/0098-national-jurisprudence-gold-coverage/tasks.md)
- [evidência live dos diretórios CNJ](../provider-discovery/national-directory-live-20260908.json)

Regenerar com:

```powershell
python tools/build_national_source_task_matrix.py --write
```

A matriz enumera os 27 Tribunais de Justiça em CJPG/CJSG, TRF1–TRF6/CJF,
STF/STJ/STM/TNU/TST/TSE/CNJ, TRT1–TRT24, TSE/TREs, TJMs e TCEs condicionais,
TCMs e 59 superfícies adicionais declaradas pelo Juscraper (`CPOPG`, `CPOSG` e
`detail`). Linhas sem fonte oficial confirmada ficam `discovery_pending`;
superfícies do Juscraper sem semântica comprovada ficam condicionais, e
bloqueios, desafios e indisponibilidade continuam explícitos — nunca são
convertidos em resultados vazios.
