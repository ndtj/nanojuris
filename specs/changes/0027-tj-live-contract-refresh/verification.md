# Verification

Status: `verified`

## Resultados

## Evidência inicial

- Discovery: `python tools/discover_all_providers.py --live --sources <26 tj*> --max-pages 2 --max-depth 0 --timeout 8 --delay 0.35 --output docs/provider-discovery/tj-provider-sweep-20261012.json`
- Resultado: 26 observados; 0 sem observação; 87 rotas declaradas; 2147
  candidatas observadas; 172 filtros declarados; 201 observados; 5 fontes com
  sinais de controle de acesso.

## Verificação parcial

- `PYTHONPATH=src python -m pytest tests/test_tjsp_eproc_jurisprudencia.py tests/test_eproc_jurisprudencia_federal.py tests/test_state_eproc_jurisprudencia.py tests/test_provider_contracts.py tests/test_provider_documentation.py tests/test_provider_coverage.py -q`
  — **48 passed**.
- A rota GET de formulário foi adicionada às capabilities TJSP eproc e à
  família eproc compartilhada por TJRJ/TJSC; os dossiês e o catálogo gerado
  foram sincronizados.

## Resultados finais

- `PYTHONPATH=src python -m pytest -q` — **877 passed, 9 skipped**.
- `python -m ruff check src tests examples tools` — passed.
- `python -m ruff format --check src tests examples tools` — 204 files already formatted.
- `python -m mypy src` — passed.
- `python -m build` — sdist and wheel built successfully.
- `python tools/validate_sdd.py` — passed.

PR #34 foi aberto a partir do commit `0dd5d9b`; todos os checks remotos
(Python 3.10–3.13, frontend, extras/wheel, CodeQL e análise Python) passaram.
O merge permanece condicionado ao estado final do PR. Nenhum bypass de
CAPTCHA, WAF, login, robots ou rate limit foi implementado.

## Rastreabilidade

Lint, suíte completa, validação SDD e verificação final de documentação ainda
serão registrados antes do PR.
