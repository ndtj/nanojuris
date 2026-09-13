# Verification

## Resultados

- `python -m pytest -q tests/test_tce_sp_jurisprudencia.py` — 6 passed.
- `python -m ruff check src/nanojuris/providers/tce_sp_jurisprudencia.py tests/test_tce_sp_jurisprudencia.py` — passed.
- O teste usa uma URL de boletim observada no HTML fixture; nenhuma chamada
  externa, CAPTCHA ou alteração de produção foi feita neste pacote.

## Rastreabilidade

| Requisito | Evidência |
|---|---|
| REQ-001 | `test_tce_sp_fetches_observed_bulletin_document` |
| REQ-002 | `fetch_document_reference` e `TransportPolicy` |
| REQ-003 | validação compartilhada de transporte/MIME/allowlist |
| REQ-004 | contrato e limitações do provider |
