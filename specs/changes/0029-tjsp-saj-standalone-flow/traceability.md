# Traceability

| Requirement | Implementation/evidence | Verification |
| --- | --- | --- |
| REQ-001 | standalone script omits control POST | source review + live run |
| REQ-002 | explicit `access_control_required` state | offline test + live output |
| REQ-003 | `_find_result_root` and `_with_results` | parser tests |
| REQ-004 | official host validation before POST | code review |
| REQ-005 | TJSP docs, sweep and smoke output | documentation audit + CI |
