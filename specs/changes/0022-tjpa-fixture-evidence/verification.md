# Verification

Status: `verified_local`

## Resultados

```text
pytest -q tests/test_initial_json_providers.py
29 passed
ruff check src/nanojuris/providers/tjpa_jurisprudencia_bff.py tests/test_initial_json_providers.py
passed
python tools/validate_sdd.py
passed
```

No production or live external state was changed.

## Results

The versioned success fixture is parsed offline and confirms the canonical id,
rapporteur, ISO publication date, raw publication date and public full text.

## Rastreabilidade

| Requirement | Evidence | Status |
| --- | --- | --- |
| REQ-001 | fixture JSON and parser invocation | passed |
| REQ-002 | `parse_tjpa_search_response` assertion | passed |
| REQ-003 | normalized/raw field assertions | passed |
