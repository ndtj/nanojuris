# Verification

Implementation and tests are recorded in `src/nanojuris/providers/tjpr_jurisprudencia.py`
and `tests/test_tjpr_jurisprudencia.py`. The public TJPR form was inspected
with a bounded GET on 2026-09-07; it returned HTTP 200 and the fields
`idComarca`, `idRelator`, `idOrgaoJulgador`, `idClasseProcessual`,
`idAssunto`, and `idsTipoDecisaoSelecionadosString`.

Commands are run after implementation and results are recorded in the handoff
message. No commit, push, publication, deploy, or production change is made.

## Resultados

- `python -m pytest -q tests/test_tjpr_jurisprudencia.py`: passed.
- `python -m ruff check src/nanojuris/providers/tjpr_jurisprudencia.py`: passed.
- `python -m mypy src`: passed in the repository gate.
- Numeric-ID rejection, judgment-date mapping, pagination and detail behavior
  are covered by the focused tests.

## Rastreabilidade

| Critério | Evidência |
|---|---|
| AC-001 | `src/nanojuris/providers/tjpr_jurisprudencia.py` and `tests/test_tjpr_jurisprudencia.py` |
| Fonte oficial | `docs/source-contracts/tjpr_jurisprudencia.md` |
| Validação bounded | `docs/provider-discovery/tjpr-cjpg-route-live-20260907.json` |
