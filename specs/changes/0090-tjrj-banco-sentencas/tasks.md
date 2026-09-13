# Tasks

- [x] **T001** confirmar rota oficial e escopo de primeiro grau.
- [x] **T002** implementar parser bounded de PDF e anotações allowlisted.
- [x] **T003** implementar filtros locais, identidade canônica e total desconhecido.
- [x] **T004** integrar provider, configuração, catálogo e cliente.
- [x] **T005** criar fixture sanitizada e testes de sucesso/filtro/escopo.
- [x] **T006** validar chamada live do índice e classificar documento 503.
- [x] **T007** revalidar documento público quando a fonte voltar a responder.
  A rechecagem bounded de 2026-09-08 confirmou o índice oficial em HTTP 200;
  o primeiro documento continuou HTTP 503 e foi preservado como
  `source_unavailable`, sem retry loop ou bypass. Evidência:
  `docs/provider-discovery/tjrj-banco-sentencas-live-20260908.json`.
- [ ] **T008** decidir promoção de coleção curada após revisão humana.
