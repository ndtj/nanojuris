# Verification

## Evidência inicial

- Matriz runtime: 44 providers, 41 com busca unificada.
- Smoke live bounded registrado em `docs/provider-discovery/provider-live-search-smoke.json`.
- Discovery de rotas/filtros registrado em `docs/provider-discovery/all-provider-sweep.json`.

## Gates

Os comandos serão atualizados após cada lote de maturação:

```bash
python tools/audit_unified_contract.py
pytest tests/test_unified_contract_audit.py
pytest -q
python tools/validate_sdd.py
```

## Resultados

- `python tools/audit_unified_contract.py`: aprovado; 44 runtime, 41 unificados, 33/44 válidos no snapshot live.
- Discovery aprofundado: 44/44 runtime e 9/9 candidates observados; 3.169 rotas, 299 filtros observados e 91 TODOs runtime ainda rastreáveis.
- `pytest -q tests/test_unified_contract_audit.py tests/test_audit_regressions.py tests/test_client_exporters.py`: aprovado; 38 testes.
- `pytest -q`: aprovado; 713 testes, 14 skips opcionais (Playwright/FastAPI/live opt-in).
- `python tools/validate_sdd.py`: aprovado.
- `python -m compileall -q src tools tests`: aprovado.
- `git diff --check`: aprovado; somente avisos de normalização CRLF preexistentes.
- O gate completo exigiu permissão de escrita temporária no ambiente Windows; a limitação não pertence ao código do projeto.

## Rastreabilidade

Os requisitos estão ligados ao design, às tarefas e a `traceability.md`. A fase permanece `in_progress` enquanto houver providers sem classificação de filtro, completude, texto integral ou evidência suficiente.
