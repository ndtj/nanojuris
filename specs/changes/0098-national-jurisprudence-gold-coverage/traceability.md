# Rastreabilidade

| Requisito | Tarefas | Evidência de fechamento |
| --- | --- | --- |
| REQ-001/002 | T002–T005 | registro e hashes regenerados |
| REQ-003/013 | T006–T011 | evidence record, contrato oficial e diff Juscraper |
| REQ-004/008 | T012–T016, T026–T030 | testes de filtros, paginação e envelope |
| REQ-005/007 | T015, T017–T025 | fixture, DocumentReference e SourceTrace |
| REQ-006 | T009, T019–T020, T027 | estados de acesso e total |
| REQ-009/010 | T026–T029, T042/T046 | manifest de promoção e decisão humana |
| REQ-011/012 | T031–T036 | smoke, cache, drift e rollback |
| REQ-014 | T033–T034, T042 | threat model, redaction e retenção |
| REQ-015 | T043–T045 | handoff, suíte e auditoria final |
| REQ-001/003 | T047–T055 | matriz nacional gerada, diretórios oficiais e backlog por família |
| REQ-006/013 | T056–T057 | descoberta oficial, chamada live bounded e classificação de bloqueio |
| REQ-004/005/007 | T058 | contrato, fixtures, inteiro teor e qualidade por fonte |
| REQ-008/009/010 | T059–T060 | smoke federado, promoção técnica e reconciliação de estados |

Os critérios AC-001–AC-012 são verificados no mesmo conjunto de tarefas; a
ausência de evidência impede marcar o critério como concluído.

O inventário detalhado por autoridade e superfície está em
`national-source-task-matrix.json`; ele é regenerado pelo script
`tools/build_national_source_task_matrix.py` e não deve ser editado manualmente.
