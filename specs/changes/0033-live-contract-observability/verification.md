# Verificação

Status: verified_with_limitations — runner, amostra bounded, redaction,
runbook e métricas locais concluídos; integração com backend gerenciado não faz
parte do ciclo sem deploy.

## Resultados

| Gate | Estado | Evidência |
| --- | --- | --- |
| policy/budget | passed | `ProbePolicy` exige allowlist e orçamento positivo |
| classificação | passed | `tests/test_observability_governance.py` e `validation.py` |
| redaction | passed | `run_allowlisted_probe` remove mensagem sensível e conteúdo |
| runbook/alertas | passed (local) | `docs/operations/provider-incident-runbook.md` |
| amostra bounded | passed | evidências live TJES, TJRN e TJTO de 2026-09-02 |
| catálogo | passed | métricas pontuais, hashes e status gerados offline |
| operação contínua | limited | runner local e artefatos são retomáveis; backend gerenciado requer ambiente de produção |

## Rastreabilidade

REQ-001 a REQ-008 possuem implementação ou evidência local; a operação contínua
fica limitada ao runner local e não autoriza deploy ou coleta em escala.
