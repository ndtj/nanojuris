# Verification

Status: `verified_local`

## Resultados

```text
pytest -q tests/test_tce_pr_viajuris.py
5 passed
ruff check src/nanojuris/providers/tce_pr_viajuris.py tests/test_tce_pr_viajuris.py
passed
python tools/validate_sdd.py
passed
```

Nenhuma chamada live ou alteração de produção foi realizada.

## Results

The fixture covers semicolon parsing, dates, official URL filtering, local
search, catalog metadata and HTTP/schema failures.

## Rastreabilidade

| Requirement | Evidence | Status |
| --- | --- | --- |
| REQ-001 | `_archive_url` and `_download` | passed |
| REQ-002 | `parse_viajuris_csv` and fixture | passed |
| REQ-003 | `_row_to_result` | passed |
| REQ-004 | `get_catalog` and classified errors | passed |
