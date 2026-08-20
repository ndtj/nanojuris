# Verification

## Local

```bash
python -m compileall -q src tools tests
pytest -q -p no:cacheprovider tests/test_provider_discovery.py tests/test_parsing.py
python tools/validate_sdd.py
```

## Live bounded

```bash
python tools/discover_all_providers.py --live --max-pages 3 --max-depth 1 --timeout 8
```

O relatório deve ser revisado por provider. O comando não é uma autorização para
contornar controles de acesso nem para transformar indisponibilidade em zero.

## Resultados

- Sweep live bounded aprofundado: 44/44 providers runtime e 9/9 candidates documentais observados; 3.169 rotas candidatas, 299 campos de filtro e 11 sinais de controle de acesso.
- Testes focados de discovery/parser/route probe: 33 passed.
- Suite completa local: 708 passed, 14 skipped; os skips são dependências opcionais e testes live opt-in.
- Suite completa com live opt-in: 716 passed, 7 skipped; os skips restantes são apenas Playwright/FastAPI opcionais.
- A compatibilidade `StoreStats.decisions` foi restaurada após a suite detectar a regressão no fluxo MCP de coleta.

## Rastreabilidade

- AC-001/002: `docs/provider-discovery/all-provider-sweep.json`, campo `providers` e `metrics.statuses`.
- AC-003/004: `contract_comparison`, `observed_routes`, `observed_filters`.
- AC-005: `_materialize_endpoint` e interpretação GET-only do executor.
- AC-006: campo `todo` por provider e `all-provider-sweep.md`.
- AC-007: `tests/test_provider_discovery.py`, replay/evidence local.
- AC-008: comandos acima e testes live opt-in existentes.
