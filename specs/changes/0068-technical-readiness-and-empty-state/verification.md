# Verification

## Resultados

- `python -m pytest -q`: 1.162 passed, 23 skipped.
- Smoke live bounded (`tests/*live*.py` com flags públicas): 26 passed.
- `python tools/validate_sdd.py`: `SDD validation passed`.
- `python -m ruff check src tests tools`: `All checks passed`.
- `python -m ruff format --check src tests tools`: 279 files formatted.
- `python -m mypy src`: 114 source files sem erros.
- `python -m compileall -q src tools tests`: aprovado.
- Manifesto técnico: 25 fontes prontas e habilitadas após decisão operacional;
  fontes bloqueadas/inconclusivas permanecem fora da promoção.
- Regressão de total desconhecido: `python -m pytest -q
  tests/test_tjpi_juspi.py tests/test_tjpr_jurisprudencia.py` — 29 passed.
- Reconciliação da matriz: `python -m pytest -q
  tests/test_surface_state_registry.py` — 6 passed; o manifesto técnico é
  consumido sem habilitar candidatos ou fontes bloqueadas.
- Regressão de memória adaptativa: `python -m pytest -q
  tests/test_tjpi_juspi.py tests/test_adaptive_selectors.py` — 46 passed; uma
  resposta vazia não reutiliza cards de uma página anterior.
- Envelope TJSP/CJSG: `python -m pytest -q tests/test_tjsp_cjsg.py` — 21
  passed; resultados e vazios expõem completude, total conhecido e estados
  públicos de acesso/extração sem reutilizar memória obsoleta.
- Regressão TJSP/CJPG: `python -m pytest -q tests/test_tjsp_cjpg.py` — 16
  passed; resposta vazia não reutiliza linhas de uma página anterior e mantém
  `total_known=False` quando o contador não aparece.
- Regressão TJTO: `python -m pytest -q tests/test_tjto_jurisprudencia.py` — 17
  passed; resposta vazia não reutiliza cards de uma página anterior e mantém
  `total_known=False` quando o contador não aparece.
- Gate de federação: `python -m pytest -q tests/test_surface_state_registry.py`
  — 6 passed; somente providers com modo `enabled` no manifesto são marcados
  como federados.

Nenhuma alteração de produção, publicação ou deploy foi realizada.

## Rastreabilidade

| Requisito | Evidência |
|---|---|
| REQ-001–REQ-003 | AC-001/AC-002 e testes de health/validação/federação |
| REQ-004 | Manifesto técnico e teste de promoção |
| REQ-005 | Varredura live e classificação explícita de falhas |
| REQ-006 | Parsers TJPI/TJPR e testes de contador ausente |
| REQ-007 | `build_surface_state_registry.py` e teste de reconciliação |
| REQ-008 | Parser TJPI e regressão de memória de seletores adaptativos |
| REQ-009 | Parser TJSP/CJSG e testes de envelope/estado vazio |
| REQ-010 | Parser TJSP/CJPG e teste de memória/contador ausente |
| REQ-011 | Parser TJTO e teste de memória/contador ausente |
| REQ-012 | Registro de superfícies consulta o modo do manifesto técnico |
