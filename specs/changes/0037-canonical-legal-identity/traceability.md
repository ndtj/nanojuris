# Rastreabilidade — identidade jurídica

| Requisito | Critério | Tarefa | Evidência | Estado |
| --- | --- | --- | --- | --- |
| REQ-001, REQ-002, REQ-003, REQ-004 | AC-001, AC-002 | T01–T04 | `src/nanojuris/identity.py`, `tests/test_identity.py`, `tests/fixtures/identity_collision_corpus.json` | pass; T05 provider migration pending |
| REQ-005, REQ-006, REQ-009 | AC-003, AC-004 | T03, T04, T07 | `IdentityMatch`, `tests/test_identity.py` | match, corpus, propriedades e guardas de mutação pass |
| REQ-007, REQ-008 | AC-005 | T05, T06 | `src/nanojuris/store.py`, `src/nanojuris/exporters/`, `tests/test_store.py`, `tests/test_client_exporters.py` | store/export roundtrip pass; T05 provider migration pending |
