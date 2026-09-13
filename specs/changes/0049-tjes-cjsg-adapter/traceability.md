# Rastreabilidade

| Requisito | Evidência |
| --- | --- |
| REQ-001/002/003/006 | `src/nanojuris/providers/tjes_jurisprudencia.py` |
| REQ-004/005 | tratamento HTTP e limite no provider |
| REQ-007 | `tests/test_tjes_jurisprudencia.py` e fixtures sanitizadas |
| REQ-008 | mudança local; sem deploy/push |

| Critério | Teste |
| --- | --- |
| AC-001/002 | parser de sucesso e página vazia |
| AC-003 | core, total, página e identidade inválidos |
| AC-004 | matriz de erros HTTP e `SourceTrace` |
| AC-005 | registro no `NanoJurisClient` |
| AC-006 | geradores de catálogo e matriz |
