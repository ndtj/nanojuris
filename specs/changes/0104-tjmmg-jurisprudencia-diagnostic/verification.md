# Verificação — TJMMG bounded

- Evidência live: `docs/provider-discovery/tjm-mg-jurisprudencia-api-live-20260909.json`.
- Fixtures: `tests/fixtures/tjmmg_metadata.json` e
  `tests/fixtures/tjmmg_search.json`.
- Testes: `tests/test_tjmmg_jurisprudencia_api.py` (9 aprovados).
- Classificação: contrato público bounded por número/janela fechada, texto na
  collection e PDF oficial por filename; buscas amplas permanecem rejeitadas.
- Decisão: runtime opt-in, não federado por padrão.

Comandos de verificação:

```text
python -m pytest -q tests/test_tjmmg_jurisprudencia_api.py
python -m ruff check src/nanojuris/providers/tjmmg_jurisprudencia_api.py tests/test_tjmmg_jurisprudencia_api.py
```

Replay live bounded (2026-09-10, sem persistir corpo): número exato retornou
um registro `TJMMG`, `degree=second`, `collection=CJSG`, com texto e URL de
documento; a rota PDF retornou `application/pdf`, 426555 bytes e extração
`complete`. Os tamanhos e o hash estão registrados na evidência JSON.
- ## Resultados

## Revalidação live bounded — 2026-09-11

O mesmo número exato retornou HTTP 200, uma decisão de segundo grau/CJSG,
texto integral e URL de documento. O hash da resposta e os metadados sanitizados
estão em `docs/provider-discovery/tjm-mg-jurisprudencia-api-live-20260911.json`.
O contrato permaneceu estável; o provider continua opt-in porque a fonte não
oferece paginação server-side e buscas amplas não são bounded.

- Metadata retrieval passed within the safe limit.
- Exact-number and closed-date queries returned bounded JSON collections.
- Empty collection is explicit only for a bounded query; oversized responses
  remain errors.
- PDF route returned a valid `%PDF` response and canonical document validation
  passed with a sanitized fixture.
- The provider remains opt-in and is not federated by default.

- ## Rastreabilidade

| Requirement | Evidence |
|---|---|
| AC-001 | `tests/test_tjmmg_jurisprudencia_api.py` metadata test |
| AC-002 | bounded collection parser test |
| AC-003 | authoritative empty test |
| AC-004 | oversized-response test |
| AC-005 | envelope/schema test |
| AC-006 | PDF canonical-document test |
| AC-007 | candidate registry and `supports_unified_search=false` |
