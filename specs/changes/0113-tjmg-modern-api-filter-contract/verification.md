# Verification - SDD 0113

## Resultados

- Implementation: `src/nanojuris/providers/tjmg_jurisprudencia.py`.
- Tests: `tests/test_tjmg_jurisprudencia.py` (8 passed in the focused run).
- Existing bounded public evidence: `docs/provider-discovery/tjmg-modern-api-live-20260907.json` and `docs/provider-discovery/tjmg-modern-api-live-recheck-20260911.json`.

- `types`, document type, decision type, comarca and subject are now reported
  with the semantics actually implemented by the API payload.
- `exact_phrase` and `all_words` are translated through the free-text field;
  `any_words` and `without_words` are rejected before network I/O.
- Type labels are de-duplicated and canonical aliases remain supported.
- Legacy CAPTCHA behavior and second-degree scope are unchanged.

## Gates

Focused tests, Ruff, mypy, compileall, SDD validation and the full repository
suite were executed during this cycle. No commit, push, release, deploy or
production change was performed.

## Rastreabilidade

| Critério | Implementação/teste | Evidência |
|---|---|---|
| AC-001/AC-002 | `get_capabilities` e `_validate_query` | `src/nanojuris/providers/tjmg_jurisprudencia.py` |
| AC-003 | `_build_modern_payload` | `tests/test_tjmg_jurisprudencia.py` |
| AC-004 | escopo, paginação e detalhe existentes | evidências modernas live do TJMG |
| AC-005 | fixtures e suíte focada | `tests/test_tjmg_jurisprudencia.py` |
