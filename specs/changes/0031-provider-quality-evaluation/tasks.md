# Tarefas

- [x] T01 — formalizar esquema do scorecard.
- [x] T02 — implementar invariantes e golden comparator.
- [x] T03 — criar fixtures transversais de falha.
- [x] T04 — avaliar todos os runtime e registrar gaps.
- [x] T05 — adicionar gate de CI sem depender de rede.
- [x] T06 — revisar falsos positivos e estabilidade.
- [x] T07 — integrar relatório ao catálogo.
- [x] T08 — registrar aceite do operador para os tiers técnicos por provider;
  a classificação completa está em `docs/quality/provider-quality.json` e o
  manifesto de promoção separa claramente tier técnico de habilitação
  federada. Providers abaixo do gate permanecem opt-in/bloqueados.

Dependência: T01 -> T02 -> T03 -> T04 -> T05 -> T06 -> T07 -> T08.
