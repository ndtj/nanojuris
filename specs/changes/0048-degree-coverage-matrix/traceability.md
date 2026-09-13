# Rastreabilidade

| Requisito | Implementação / evidência |
| --- | --- |
| REQ-001/003 | `CoverageSurface` e invariantes em `src/nanojuris/coverage_matrix.py` |
| REQ-002 | gerador cria CJPG/CJSG para cada TJ em `build_degree_matrix()` |
| REQ-004/006 | declarações de superfícies equivalentes e grau `mixed` |
| REQ-005/008 | validação de status/queryable e classificação explícita |
| REQ-007 | linhas agregadas de lacuna por unidade judicial |
| REQ-009 | `tools/build_degree_coverage.py` sem rede |
| REQ-010 | mudança local; nenhum deploy/push |
| REQ-011 | 27 linhas TRE de segundo grau geradas a partir de `COURTS` |

| Critério | Teste |
| --- | --- |
| AC-001 | `test_matrix_has_cjpg_and_cjsg_for_all_state_tjs` |
| AC-002 | `test_matrix_rejects_invalid_collection_degree` |
| AC-003/004 | `test_summary_exposes_branch_degree_and_gaps` |
| AC-005 | `test_mixed_provider_does_not_cover_cjpg_or_cjsg` |
| AC-006 | `test_degree_matrix_artifact_matches_builder` |
| AC-007 | suíte `tests/test_coverage_matrix.py` |
| AC-008 | comandos registrados em `verification.md` |
| AC-009 | `test_matrix_lists_all_tres_as_second_degree_surfaces` |
