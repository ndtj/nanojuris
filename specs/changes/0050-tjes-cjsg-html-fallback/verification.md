# Verificacao

Status: verified — fallback, fixtures e gates locais concluídos.

## Resultados

- [x] Fallback implementado em `tjes_jurisprudencia` com precedencia plano ->
  HTML e marcadores de origem em `raw`.
- [x] Fixture HTML-only e teste de regressao aprovados (`14 passed`, live
  opt-in `1 passed`).
- [x] Suite completa: `986 passed, 12 skipped`.
- [x] Ruff, format check, mypy de `src`, mypy do gerador de matriz,
  `compileall`, `git diff --check` e `validate_sdd.py` aprovados.
- [x] Nenhuma publicacao, push, deploy ou alteracao em producao.

## Rastreabilidade

Os resultados finais serao preenchidos apos a execucao de `pytest`, Ruff,
mypy, `compileall` e `validate_sdd.py`.
