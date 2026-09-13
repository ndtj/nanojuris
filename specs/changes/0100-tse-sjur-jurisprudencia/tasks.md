# Tasks — TSE SJUR jurisprudência textual

- [x] T001 registrar rota pública e limites observados (REQ-001/007)
- [x] T002 implementar DSL conservadora e transporte allowlisted (REQ-001/002/006)
- [x] T003 mapear campos canônicos e preservar `raw` (REQ-003/004)
- [x] T004 classificar vazios, bloqueios, rate-limit e schema drift (REQ-005)
- [x] T005 criar fixtures sanitizadas e testes de contrato (AC-002/003/004)
- [x] T006 executar smoke live bounded e registrar hash/limitações (AC-006)
- [x] T007 validar paginação em rota oficial sem contornar controles — as
  páginas 1, 2 e 3, com `tamanho=3`, retornaram os mesmos 132 registros; as
  páginas 1 e 2 também produziram o mesmo hash. O contrato foi fechado como
  `pagination_mode=none`/janela única, sem afirmar paginação ou completude de
  corpus além da resposta recebida.
- [x] T008 localizar e validar rota pública de documento/PDF
- [x] T009 decidir promoção técnica somente após T007/T008 e gate de qualidade —
  decisão técnica: promover para runtime opt-in, mantendo
  `supports_unified_search=false` e `federation_status=disabled`, porque a
  fonte oferece uma resposta única sem paginação remota segura e não há
  evidência agregada de completude do corpus.
