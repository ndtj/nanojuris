# Verificação

Status: `verified_local`

## Complemento T06

`pytest -q tests/test_pagination.py tests/test_provider_contracts.py` passou
com 13 testes. A paginação base agora deduplica por identidade contextual
(fonte, tribunal, tipo e número ou hash de metadados), preservando registros
distintos quando a fonte omite ou repete o ID.

## Resultados

| Execução | Resultado |
|---|---|
| inventário offline de providers | passed — 55 entradas de catálogo, 45 runtime, 9 candidatos, 1 família |
| matriz de contrato unificado | passed — 41 unificados, 4 excluídos por capability declarada |
| `pytest -q tests/test_provider_contracts.py tests/test_provider_state_fixtures.py tests/test_unified_contract_audit.py tests/test_source_contracts.py tests/test_provider_coverage.py tests/test_provider_documentation.py tests/test_all_provider_discovery.py tests/test_initial_json_providers.py` | passed — 56 testes |
| `PYTHONPATH=. pytest -q` | passed — 793 testes, 8 skips, 1 aviso existente |
| `ruff check src tests tools` | passed |
| `python -m compileall -q src tools tests` | passed |
| `python tools/validate_sdd.py` | passed |

O inventário identificou 9 candidatos sem runtime, 31 dossiês sem referência
explícita de fixture e 38 dossiês com itens documentais abertos. Esses itens
permanecem lacunas declaradas, não foram preenchidos por inferência.

## Riscos residuais

Testes locais não comprovam disponibilidade live, mudanças recentes de HTML,
rate limits ou controles de acesso das fontes.

## Rastreabilidade

| Requisito | Evidência | Estado |
|---|---|---|
| REQ-001 | inventário offline e matriz de providers | passed |
| REQ-002 | testes de contratos e estados | passed |
| REQ-003 | testes de canonicalização, traces e falhas | passed |
| REQ-004 | lacunas e candidatos explicitamente listados | passed |
| REQ-005 | suíte, lint, compilação e SDD | passed |
