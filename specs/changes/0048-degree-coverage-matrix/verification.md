# Verificação

## Estado inicial

- Catálogo institucional: 94 autoridades.
- TJs estaduais: 27.
- `CourtInfo` marcava 10 TJs como implementados, mas o registro runtime
  continha providers adicionais não reconciliados por autoridade.
- Topologia central atribuía `degree="unknown"` às coleções de tribunal.

## Resultados

- [x] Gerador offline executado: 148 superfícies, 125 obrigatórias e 107
  lacunas (inclui uma linha própria para cada TRE).
- [x] A matriz contém 27 linhas CJPG e 27 linhas CJSG.
- [x] Testes específicos da matriz aprovados: 9 casos neste ciclo.
- [x] Suíte completa aprovada: 972 passed, 11 skipped.
- [x] Ruff, mypy e compileall aprovados para o novo módulo e gerador.
- [x] Decisão do operador para uso técnico local/federado registrada em
  `docs/operations/provider-promotion-approvals-20260905.json`.

## Rastreabilidade

| Critério | Evidência |
| --- | --- |
| AC-001/002 | `tests/test_coverage_matrix.py` |
| AC-003/004 | resumo e linhas por ramo em `degree-coverage-matrix-20260901.json` |
| AC-005 | teste de provider `mixed` sem promoção a CJPG/CJSG |
| AC-006 | comparação do artefato com `tools/build_degree_coverage.py` |
| AC-007 | suíte focada da matriz |
| AC-009 | teste que enumera os 27 TREs como segundo grau |

## Comandos e resultados

```text
python tools/build_degree_coverage.py
python -m pytest -q tests/test_coverage_matrix.py tests/test_brazil.py tests/test_topology.py
python -m pytest -q
ruff check src/nanojuris/coverage_matrix.py tools/build_degree_coverage.py tests/test_coverage_matrix.py src/nanojuris/__init__.py
mypy src
mypy tools/build_degree_coverage.py
ruff check src tools tests
ruff format --check src tools tests
python -m compileall -q src tools
python tools/validate_sdd.py
```

Resultados: gerador concluído; 9 testes específicos da matriz aprovados; suíte completa
`972 passed, 11 skipped`; Ruff, mypy, compileall e validação SDD aprovados.
Os testes live continuam opcionais e não foram executados nesta mudança.

`mypy src tools` completo continua apontando três erros preexistentes em
`tools/build_selector_fingerprints.py` e `tools/discover_all_providers.py`; o
escopo desta mudança foi verificado com `mypy src` e com o gerador alterado.

## Gates pendentes

Os gates locais desta rodada estão concluídos. A decisão do operador cobre o
uso técnico local/federado; a matriz continua sem afirmar cobertura nacional
onde não existe contrato ou evidência live. Nenhum gate autoriza deploy, push
ou mudança de produção.

Nenhuma etapa desta especificação autoriza deploy, push ou mudança de produção.
