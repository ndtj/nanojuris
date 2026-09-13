# Rastreabilidade - busca federada

| Requisito | Criterio | Tarefa | Evidencia | Estado |
| --- | --- | --- | --- | --- |
| REQ-001, REQ-002, REQ-008, REQ-009 | AC-001, AC-004 | T01-T03 | planner, semantica e planos por fonte | pass |
| REQ-003, REQ-004 | AC-002, AC-003 | T04-T06 | merge/ranking global determinístico, sem comparar relevância nativa | pass |
| REQ-005, REQ-006, REQ-010 | AC-003, AC-006 | T03-T06 | cursor, completude global e outcomes por fonte | pass |
| REQ-007 | AC-003 | T04, T05 | deduplicação pela identidade 0037, sem merge incerto | pass |
| REQ-001-REQ-010 | AC-005 | T06, T07 | testes e docs opt-in; facade legada preservada | pass |

O status `pass` cobre a fundação offline e a API opt-in; não declara cobertura
de todos os providers nem integração federada em produção.
