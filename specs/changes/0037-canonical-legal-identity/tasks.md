# Tarefas

- [x] T01 - inventariar IDs e dedup atuais em modelos, canonical e store.
- [x] T02 - definir tipos, namespaces, versoes e regras por categoria.
- [x] T03 - criar corpus de colisao e golden relationships.
- [x] T04 - implementar identity resolver e match explicavel.
- [x] T05 - migrar dois providers com multiplas decisoes/republicacoes; o teste de integracao usa TJES CJPG e TJSP CJPG com IDs nativos estaveis e republicacao idempotente.
- [x] T06 - provar roundtrip em store e exports.
- [x] T07 - executar property, mutation e compatibility tests.
- [x] T08 - documentar migracao e registrar decisao de API publica.

Evidencia de T05: `tests/test_identity_provider_migration.py` prova duas
decisoes distintas em cada provider e a mesma decisao republicada mantendo a
identidade legal.
