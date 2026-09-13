# Rastreabilidade — autopilot

| Requisito | Critério | Tarefa | Evidência | Estado |
| --- | --- | --- | --- | --- |
| REQ-001 | AC-001, AC-002 | T01, T03, T04, T11 | baseline/workpacks dinâmicos | verified |
| REQ-002 | AC-001 | T03, T04 | lifecycle fields | verified |
| REQ-003 | AC-002, AC-003, AC-004 | T02, T03, T05, T11, T12 | state preservation/fingerprint tests | verified |
| REQ-004 | AC-004 | T03, T04 | priority queue | verified |
| REQ-005 | AC-005, AC-006 | T02, T08, T10, T12 | DoD/verification | pending |
| REQ-006 | AC-005, AC-006 | T02, T09, T12 | deferimento revisável | verified_design |
| REQ-007 | AC-003, AC-006 | T02, T05 | checkpoint test/runbook | verified_design |
| REQ-008 | AC-008 | T02, T08 | bounded policy | pending |
| REQ-009 | AC-006, AC-008 | T02, T10 | human gate | pending |
| REQ-010 | AC-003 | T03, T05, T11 | regeneration/fingerprint test | verified |
| REQ-011 | AC-004, AC-005 | T11, T12 | terminal state schema | verified |
| REQ-012 | AC-006 | T13 | dependency-aware queue | pending |
| REQ-013 | AC-009 | T14 | legacy state migration test | verified |
| REQ-014 | AC-010 | T15, T16 | complete_provider_workpacks.py | verified |
| REQ-015 | AC-005, AC-010 | T15, T16 | terminal disposition classifier | verified |
| REQ-016 | AC-011 | T16, T17 | generated workpack completion test | verified |
| REQ-001–REQ-013 | AC-007 | T05, T10, T11, T14 | Ruff, mypy, pytest e validate_sdd | verified |
| REQ-014–REQ-016 | AC-007 | T17 | focused and full test gates | verified |
