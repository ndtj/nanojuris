# Tarefas

- [x] T01 - construir matriz de impacto das interfaces (`docs/operations/interface-impact-matrix-20260902.json/.md`).
- [x] T02 - definir flags, shadow e rollback por provider.
- [x] T03 - automatizar auditoria de docs e catalogo.
- [x] T04 - implementar checagens de compatibilidade e depreciacao.
- [x] T05 - produzir SBOM e provenance da release.
- [x] T06 - executar release rehearsal sem producao.
- [x] T07 - registrar a decisao operacional do usuario para fontes publicas tecnicamente aprovadas; o artefato nao autoriza deploy ou redistribuicao.
- [x] T08 - [out_of_scope] publicar, observar e registrar rollback de release
  não foi autorizado neste ciclo; o runbook e os gates de rollback estão
  prontos para retomada após autorização explícita.
- [x] T09 - criar baseline de mypy para tools/tests sem relaxar `src`.

T08 permanece bloqueada por escopo: esta rodada nao faz push, publicacao, deploy
ou alteracao de producao.
