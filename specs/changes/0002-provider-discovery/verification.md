# Verificação

Referência: `specs/changes/0002-provider-discovery/spec.md`

## Comandos

```bash
pytest tests/test_provider_discovery.py
ruff check src/nanojuris/discovery tests/test_provider_discovery.py
mypy src/nanojuris/discovery
python tools/validate_sdd.py
```

## Matriz

| Requisito | Evidência esperada | Estado |
| --- | --- | --- |
| RF-001 | testes de response, hash, bytes e duração | passed |
| RF-002 | testes de links, forms, scripts e JSON | passed |
| RF-003 | teste opcional sem Playwright e fixtures de evento | passed |
| RF-004 | testes de allowlist, limites e redirects | passed |
| RF-005 | testes de bloqueio, timeout e indisponibilidade | passed |
| RF-006 | testes de candidatos e confiança | passed |
| RF-007 | teste de geração de artefatos | passed |
| RF-008 | teste de replay sem rede | passed |

## Resultados

Atualização de 2026-09-02: todos os requisitos RF-001..RF-008 foram
revalidados pela suíte completa (1096 passed, 12 skipped), Ruff, mypy,
compilação e `validate_sdd.py`. Os gates humanos T14/T15 permanecem
explicitamente pendentes.

| Execução | Comando | Resultado | Observação |
| --- | --- | --- | --- |
| local | `python -m compileall -q src/nanojuris/discovery` | passed | compilação sintática concluída |
| local | `pytest tests/test_provider_discovery.py` | passed | 7 testes aprovados no ambiente atual |
| local | `pytest tests/test_route_probe.py tests/test_sdd_validation.py` | passed | 19 testes aprovados |
| local | `pytest tests/test_mcp_server.py tests/test_cli.py -k "discover_provider or probe_rota or create_server"` | passed | integração CLI/MCP validada |
| local | `pytest tests/test_mcp_tools.py -k "not store"` | passed | 17 testes MCP sem store aprovados |
| local | `python tools/validate_sdd.py` | passed | validação SDD concluída |
| local | `python -m pytest -q` | passed | 1096 testes aprovados, 12 ignorados em 2026-09-02 |
| local | `python -m ruff check src tools tests` + `ruff format --check` | passed | 260 arquivos formatados |
| local | `python -m mypy src` + `python -m compileall -q src tools tests` | passed | tipagem e compilação concluídas |

## Rastreabilidade

| Requisito | Critério | Tarefa | Evidência |
| --- | --- | --- | --- |
| RF-001 | AC-001 | T1-T4 | testes de resposta e traces |
| RF-002 | AC-006 | T5 | testes de candidatos |
| RF-003 | AC-006/AC-007 | T6 | adaptador browser e teste opcional |
| RF-004 | AC-002/AC-003/AC-004 | T2-T3 | testes de política e limites |
| RF-005 | AC-005/AC-011 | T4/T11 | matriz de estados |
| RF-006 | AC-006 | T7 | candidatos de seletores |
| RF-007 | AC-009 | T9-T10 | drafts SDD e CLI |
| RF-008 | AC-008 | T8/T11 | replay offline |

## Riscos residuais

- A execução live não é necessária para validar o núcleo e deve ser explicitamente
  marcada quando usada.
- Nenhuma execução dinâmica comprova sozinha a estabilidade de um contrato.
