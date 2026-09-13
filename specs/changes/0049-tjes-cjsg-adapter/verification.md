# Verificação

## Estado inicial

`tjes_jurisprudencia` era candidato live com resposta pública, sem provider
runtime, fixtures ou contrato canônico.

## Resultados

- [x] Provider e parser implementados (`tjes_jurisprudencia`, core `pje2g`).
- [x] Fixtures sanitizadas e 13 testes offline aprovados.
- [x] Catálogo, dossiê e matriz regenerados; CJSG subiu de 6/27 para 7/27.
- [x] Gates estáticos aprovados para os arquivos alterados.
- [x] Chamada live bounded: HTTP 200, 1 registro, total 68.421; corpo não persistido.
- [x] Decisão do operador para uso técnico local/federado registrada em
  `docs/operations/provider-promotion-approvals-20260905.json`.

## Gates

Nenhuma etapa desta especificação autoriza deploy, push ou alteração em
produção. Testes live permanecem bounded e sem persistir o corpus.

Comandos: `pytest tests/test_tjes_jurisprudencia.py`, teste live com
`NANOJURIS_RUN_LIVE=1`, `ruff`, `mypy`, `compileall` e `validate_sdd.py`.

## Rastreabilidade

| Critério | Evidência |
| --- | --- |
| AC-001/002/003/004 | `tests/test_tjes_jurisprudencia.py` |
| AC-005 | `NanoJurisClient` e `tests/test_tjes_jurisprudencia.py` |
| AC-006 | catálogos e matriz gerados pelos scripts oficiais |
