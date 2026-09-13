# Traceability matrix - live intelligent search

Change: `specs/changes/0077-live-intelligent-federated-search/spec.md`

| Requirements | Criteria | Tasks | Evidence | State |
|---|---|---|---|---|
| REQ-001 to REQ-005 | AC-001, AC-002, AC-007 | T05-T13 | `test_search_intent.py`, vocabulary and golden queries | verified |
| REQ-006 to REQ-009 | AC-003, AC-004, AC-014 | T14-T22 | `test_adaptive_search.py`, stable plans | verified |
| REQ-010, REQ-011 | AC-005, AC-006 | T23-T29 | outcome and failure tests | verified |
| REQ-012 to REQ-015 | AC-007 to AC-010 | T30-T41 | `test_relevance.py`, deterministic ranker | verified |
| REQ-012 to REQ-015 | AC-017 to AC-020 | T61-T62 | benchmark schema and performance artifact | pending human labels/holdout |
| REQ-016, REQ-017 | AC-011 | T42-T46 | cross-source deduplication and near-tie tests | verified |
| REQ-018 | AC-012, AC-015 | T39, T47-T49 | library/API/browser allowlists | verified |
| REQ-019, REQ-020 | AC-010, AC-013 | T53-T57, T60 | platform contract tests for waves and freeze | verified locally |
| REQ-021 | AC-012 to AC-014 | T58-T60 | chips, reasons, source states and a11y checks | verified locally |
| REQ-022 | AC-015, AC-016 | T50, T51 | versioned cache, TTL and redaction tests | verified |
| REQ-023 | AC-016 | T63 | telemetry schema and retention policy | verified locally |
| REQ-024 | AC-024 | T63, T64 | legacy/shadow/v1, rollback and bounded smokes | verified locally |
| REQ-025 | AC-015, AC-021, AC-022 | T47-T52, T64 | API/SDK/CLI/MCP/Studio suite | verified locally |
| REQ-026 | AC-019, AC-020, AC-022 | T30-T41, T52, T64 | no-AI audit and full suite | verified |
| All | AC-023 | T64 | six-query bounded smoke and redacted report | verified locally |

## Remaining qualification

The ranking implementation is deterministic and locally tested. The required
quality claim (relative nDCG improvement, holdout validity, and human relevance
labels) is intentionally not asserted until independent legal judgments exist.
Likewise, live source failures remain source-specific outcomes and do not turn
into empty results.
