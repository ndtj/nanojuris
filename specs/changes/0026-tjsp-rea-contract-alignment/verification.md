# Verification

Status: `verified`

This file is updated after implementation with exact commands, results, live
classification and any deviations.

## Resultados

- `python tools/validate_sdd.py` — passed.
- `python -m pytest tests/test_tjsp_cjsg.py tests/test_tjsp_eproc_jurisprudencia.py -q` — 38 passed.
- `python -m pytest tests/test_provider_documentation.py tests/test_provider_coverage.py -q` — 15 passed.
- `python -m pytest -q` with `PYTHONPATH=src` — 877 passed, 9 skipped.
- `python -m ruff check src tests examples tools` — passed.
- `python -m ruff format --check src tests examples tools` — 204 files formatted.
- `python -m mypy src` — passed.
- `python -m build` — built sdist and wheel successfully.
- Live eproc bounded query — returned `total=513281`, one result, canonical
  endpoint `listar_resultados`.
- Live CJSG bounded query — raised `AccessControlRequiredError` with
  `has_recaptcha_field`, `has_uuid_captcha_field` and control-route flags;
  this is the expected fail-closed result.

## Rastreabilidade

The commands above prove `REQ-001` through `REQ-006` and `AC-001` through
`AC-004`. `AC-005` remains open until the branch/PR review and merge flow is
completed. No deviation was accepted; CAPTCHA/login bypass remains out of scope.
