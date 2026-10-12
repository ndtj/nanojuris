# Verification

Status: `verified`

## Resultados

- `PYTHONPATH=src python -m pytest tests/test_busca_saj_tjsp.py -q`: 4 passed.
- `python examples/busca_saj_tjsp.py 'dano moral' --perfil courts`: explicit
  `access_control_required`, HTTP 200, returned form and CAPTCHA present.
- `python -m pytest -q`: 884 passed, 9 skipped.
- `python -m ruff check src tests examples tools`: passed.
- `python -m ruff format --check src tests examples tools`: 207 files already formatted.
- `python -m mypy src`: passed, no issues in 94 source files.
- `python tools/validate_sdd.py`: passed.
- `PYTHONPATH=src python -m pytest tests/test_tjsp_cjsg.py tests/test_busca_saj_tjsp.py -q`: 28 passed after provider form-session alignment.
- Integrated live provider probe for `dano moral`: explicit
  `AccessControlRequiredError` with search form, reCAPTCHA, uuid and control-route
  signals; no result was presented as a false zero-result response.
- Targeted documentation/coverage/SDD tests: 16 passed.
- `python -m build`: built the sdist and wheel successfully.
- `git diff --check`: passed.
- PR #36 CI: Python 3.10-3.13, CodeQL, Workbench frontend e extras/clean wheel
  passaram.
- PR #36 foi integrado em `main` pelo commit `1d4c1b1`.

## Rastreabilidade

The checks above cover REQ-001 through REQ-005 from `spec.md`; live evidence
is bounded and does not demonstrate permanent availability.
