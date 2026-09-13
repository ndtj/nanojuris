# Tarefas

- [x] T01 — inventariar research runs, store, cache e export atuais.
- [x] T02 — definir manifest, checkpoint, version e freshness schemas.
- [x] T03 — implementar escrita atômica e retomada idempotente.
- [x] T04 — integrar identidade/versionamento 0037.
- [x] T05a — implementar limites, limpeza opt-in e ledger de tombstone seguro.
- [x] T05b — definir retenção de raw/store com política explícita da operação.
- [x] T06 — testar crash/restart, drift, duplicidade e disco cheio.
- [x] T07 - integrar completeness em exports e interfaces.
- [x] T08 — documentar limites e executar benchmark local.

Dependência: T01 -> T02 -> T03 -> T04 -> T05a -> T06 -> T07 -> T08; T05b
permanece uma decisão de operação antes de qualquer retenção destrutiva.
