# Verificação

## Comandos

```bash
python -m compileall -q src tools tests
pytest tests/test_parsing.py tests/test_normalization.py tests/test_collection.py
pytest tests/test_provider_discovery.py tests/test_provider_documentation.py
python tools/validate_sdd.py
```

## Resultados

| Execução | Comando | Resultado |
| --- | --- | --- |
| local | matriz de comparação e inventário | concluído |
| local | implementação das fundações | concluído: parsing, normalização, memória adaptativa e coleta |
| local | testes dos primitives | concluído: testes unitários e contratos TJGO/TJPR |
| local | validação SDD | concluído: `python tools/validate_sdd.py` passou |
| local | compilação | concluído: `python -m compileall -q src tools tests` passou |
| local | regressão focada | concluído: 108 testes passaram; suíte completa requer ajuste do temp do ambiente Windows |
| live | BNP, STJ dados abertos, TJBA, TJSP/CJSG | concluído: 5 testes live passaram |
| live | STJ Informativo e STJ SCON | concluído: 2 testes live passaram |
| live | CJF/TRF1, TJGO/Projudi e TJPR | TJGO/TJPR retornaram resultados com trace; CJF classificou access-control explicitamente |

## Rastreabilidade

| Requisito | Critério | Tarefa | Evidência |
| --- | --- | --- | --- |
| RF-001/RF-002 | AC-001/AC-002 | T1 | parser e fixtures |
| RF-003 | AC-003 | T2 | testes de normalização |
| RF-004 | AC-004 | T3 | memória adaptativa |
| RF-005/RF-006 | AC-005/AC-006 | T5/T6 | runner e store |
| RF-007 | AC-007 | T4/T7 | providers migrados |
| RF-008 | AC-008 | T8/T9 | CLI, MCP e gates |

## Evidência incremental

- Parser compartilhado: `src/nanojuris/parsing.py` e `tests/test_parsing.py`.
- Normalização: `src/nanojuris/normalization.py` e `tests/test_normalization.py`.
- Memória revisável: `src/nanojuris/adaptive.py` e `tests/test_adaptive.py`.
- Coleta resumível: `src/nanojuris/collection.py` e `tests/test_collection.py`.
- Providers migrados: `tjgo_projudi_jurisprudencia`, `tjpr_jurisprudencia`,
  `cjf_jurisprudencia`, `stj_informativo` e `stj_scon`.
- Interfaces: comando `coletar`, `collect_jurisprudence` no MCP e cliente Python.
