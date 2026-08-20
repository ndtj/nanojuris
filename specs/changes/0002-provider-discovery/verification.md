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
| RF-001 | testes de response, hash, bytes e duração | pending |
| RF-002 | testes de links, forms, scripts e JSON | pending |
| RF-003 | teste opcional sem Playwright e fixtures de evento | pending |
| RF-004 | testes de allowlist, limites e redirects | pending |
| RF-005 | testes de bloqueio, timeout e indisponibilidade | pending |
| RF-006 | testes de candidatos e confiança | pending |
| RF-007 | teste de geração de artefatos | pending |
| RF-008 | teste de replay sem rede | pending |

## Resultados

| Execução | Comando | Resultado | Observação |
| --- | --- | --- | --- |
| local | `python -m compileall -q src/nanojuris/discovery` | passed | compilação sintática concluída |
| local | `pytest tests/test_provider_discovery.py` | passed | 7 testes aprovados no ambiente atual |
| local | `pytest tests/test_route_probe.py tests/test_sdd_validation.py` | passed | 19 testes aprovados |
| local | `pytest tests/test_mcp_server.py tests/test_cli.py -k "discover_provider or probe_rota or create_server"` | passed | integração CLI/MCP validada |
| local | `pytest tests/test_mcp_tools.py -k "not store"` | passed | 17 testes MCP sem store aprovados |
| local | `python tools/validate_sdd.py` | passed | validação SDD concluída |

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
