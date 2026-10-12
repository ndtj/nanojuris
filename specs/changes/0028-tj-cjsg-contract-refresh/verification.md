# Verification

Status: `verified`

## Resultados

- Bounded CJSG discovery: 6 providers observed; 401 route candidates; TJAM and
  TJCE remained robots-disallowed; no access-control bypass was attempted.
- Live search smoke: TJAC 25,517; TJAL 186,132; TJMS 351,874; TJSP eproc
  513,289; TJSP CJSG returned `AccessControlRequiredError`.
- `PYTHONPATH=src python -m pytest -q`: **879 passed, 9 skipped**.
- `python -m ruff check src tests examples tools`: passed.
- `python -m ruff format --check src tests examples tools`: passed.
- `python -m mypy src`: passed.
- `python -m build`: sdist and wheel built successfully.
- `python tools/validate_sdd.py`: passed.
- `git diff --check`: passed.

## Planned checks

- bounded CJSG discovery with only declared public GET routes;
- targeted and full pytest suites;
- Ruff, mypy, build and SDD validation;
- generated documentation and provider coverage audits;
- final diff and PR/CI review.

## Rastreabilidade

The commands above verify REQ-001 through REQ-005 from `spec.md`; live route
status remains bounded by robots and source availability.
