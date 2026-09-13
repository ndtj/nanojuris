# Verification — SDD 0110

- Live bounded GET do PDF simplificado TRT9: HTTP 200, `application/pdf`,
  51.999 bytes, 23 páginas, texto extraível.
- Live bounded GET da coleção IRDR: HTTP 200, `application/pdf`, 51.516 bytes,
  25 páginas, texto extraível e números CNJ TRT9 observados.
- Nenhum cookie, credencial, CAPTCHA ou bypass foi usado; corpos brutos não são
  persistidos.
- Testes focados: `tests/test_trt9_nugepnac_jurisprudencia.py`.
- Rechecagem bounded da entrada oficial de pesquisa avancada JSF registrada em
  `docs/provider-discovery/trt9-banco-jurisprudencia-search-live-20260910.json`:
  GET e POST publicos responderam HTTP 200, mas a resposta continha somente as
  tabelas vazias e nao revelou contrato reproduzivel de busca geral. A sonda
  nao encerra T007 nem converte a fonte em vazio definitivo.
- A coleção permanece `opt_in_unified_search=true` e não é cobertura geral.

## Resultados

| Verificação | Resultado |
| --- | --- |
| Fixture/parser de precedentes | 6 testes aprovados |
| Sonda live bounded IRDR | HTTP 200, PDF 25 páginas, 3 resultados filtrados |
| Documento observado | `application/pdf`, extração `complete` |
| Ruff, mypy e compileall focados | aprovados |
| Federação padrão | desabilitada por contrato contextual |

## Rastreabilidade

| Requisito | Critério | Tarefa | Evidência | Estado |
| --- | --- | --- | --- | --- |
| REQ-001 | AC-001 | T001-T002 | adapter allowlisted + trace | passed |
| REQ-002/REQ-003 | AC-002 | T003 | parser, fixture e testes canônicos | passed |
| REQ-004/REQ-005 | AC-003 | T004 | filtros e erros explícitos | passed |
| REQ-006 | AC-004/AC-005 | T005-T006 | evidência live e manifesto opt-in | passed |
| externo | contrato de busca geral | T007 | entrada JSF alcançada, resultados gerais ainda não reproduzidos; `trt9-banco-jurisprudencia-search-live-20260910.json` | pending_external |
| humano | retenção/promoção | T008 | decisão do mantenedor | pending_human |
