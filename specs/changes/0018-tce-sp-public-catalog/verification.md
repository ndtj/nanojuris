# Verification

Status: `verified_local`

## Resultados

```text
pytest -q tests/test_tce_sp_jurisprudencia.py
passed
ruff check src/nanojuris/providers/tce_sp_jurisprudencia.py tests/test_tce_sp_jurisprudencia.py
passed
python tools/validate_sdd.py
passed
```

No production or external state was changed.

## Results

The fixture-backed catalog test validates both public collection requests,
species, counts and raw records.

## Rastreabilidade

| Requirement | Evidence | Status |
| --- | --- | --- |
| REQ-001 | `get_catalog` public route calls | passed |
| REQ-002 | TCE-SP options and groups | passed |
| REQ-003 | `ProviderCatalog.raw` and `SourceTrace` | passed |
| REQ-004 | CAPTCHA route not called | passed |
