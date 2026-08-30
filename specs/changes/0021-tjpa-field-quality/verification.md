# Verification

Status: `verified_local`

## Resultados

```text
pytest -q tests/test_initial_json_providers.py
passed
ruff check src/nanojuris/providers/tjpa_jurisprudencia_bff.py tests/test_initial_json_providers.py
passed
python tools/validate_sdd.py
passed
```

No production or live external state was changed.

## Results

Regression coverage confirms ISO dates, raw date preservation and partial
status for records without legal text.

## Rastreabilidade

| Requirement | Evidence | Status |
| --- | --- | --- |
| REQ-001 | `normalize_date` mapping | passed |
| REQ-002 | raw date fields | passed |
| REQ-003 | extraction status branch | passed |
