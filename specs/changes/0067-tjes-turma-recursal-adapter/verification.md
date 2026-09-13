# Verificacao

## Resultados

- Chamada live bounded em 2026-09-05: HTTP 200, JSON valido, documentos com
  texto inline e total declarado; corpo analisado em memoria.
- Testes offline do adapter: parser, vazio, schema drift, core incorreto,
  parametros, canonicalizacao, trace e 4xx/429/5xx.
- Teste focado: `11 passed`.
- Teste live gated: `1 passed` com `NANOJURIS_RUN_LIVE=1`.
- O provider esta registrado como `tjes_turma_recursal` e incluido na federacao
  padrao (`supports_unified_search=True`), mantendo a colecao de turma recursal
  separada dos bindings CJPG/CJSG.

## Rastreabilidade

| Requisito | Evidencia |
| --- | --- |
| REQ-001/004 | `src/nanojuris/providers/tjes_turma_recursal.py` e testes |
| REQ-002/003/005 | parser, `raw`, `SourceTrace`, identidade e canonicalizacao |
| REQ-006 | politica HTTP compartilhada e ausencia de bypass |
| AC-001 | teste live `tests/test_tjes_turma_recursal_live.py` |
| AC-002/004 | fixtures e `tests/test_tjes_turma_recursal.py` |
| AC-005 | registro no client, capability e teste opt-in |

## Gates pendentes

O escopo desta rodada autoriza o uso técnico local/federado; coleta em escala,
publicação e release continuam fora do escopo. Nenhum push, deploy ou alteração
de produção foi feito.
