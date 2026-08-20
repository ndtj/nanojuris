# Verificação

## Comandos

```bash
python tools/audit_provider_discovery_offline.py
python -m compileall -q tools/audit_provider_discovery_offline.py
pytest tests/test_provider_discovery.py tests/test_sdd_validation.py
python tools/validate_sdd.py
```

## Resultados

| Execução | Comando | Resultado |
| --- | --- | --- |
| local | `python tools/audit_provider_discovery_offline.py` | passed — 54 entradas, 9 candidates, 3 análises locais |
| local | `python -m compileall -q tools/audit_provider_discovery_offline.py tests/test_provider_discovery_audit.py` | passed |
| local | `pytest tests/test_provider_discovery_audit.py tests/test_provider_discovery.py tests/test_sdd_validation.py` | passed — 11 testes |
| local | `python tools/validate_sdd.py` | passed |

## Rastreabilidade

| Requisito | Critério | Tarefa | Evidência |
| --- | --- | --- | --- |
| RF-001 | AC-001 | T1 | relatório JSON |
| RF-002 | AC-002/AC-003 | T2 | matriz de arquivos e registro |
| RF-003 | AC-002/AC-006 | T2/T6 | candidates fora do runtime |
| RF-004 | AC-003/AC-005 | T3/T4 | métricas offline eproc |
| RF-005 | AC-004 | T6 | campo `offline_evidence_status` |
| RF-006 | AC-006/AC-007 | T5 | JSON, Markdown e validação SDD |
