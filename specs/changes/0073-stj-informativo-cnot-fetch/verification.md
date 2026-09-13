# Verification

## Resultados

- `python -m pytest -q tests/test_stj_informativo.py` — 17 passed.
- `python -m ruff check src/nanojuris/providers/stj_informativo.py tests/test_stj_informativo.py` — passed.
- O fixture usa CNOT público e não tenta acessar ou contornar a rota SCON.

## Rastreabilidade

| Requisito | Evidência |
|---|---|
| REQ-001 | mapa `result_id -> cnot_url` em `search` |
| REQ-002 | `fetch_document_reference` e `TransportPolicy` |
| REQ-003 | `acordao_url` permanece separado em `raw` |
| REQ-004 | teste de allowlist e ID desconhecido |
