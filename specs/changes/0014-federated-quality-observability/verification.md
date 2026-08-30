# Verificacao

Status: `verified_local`

## Resultados

### Complemento T06

`NanoJurisClient.search_many` agora inclui `source_completeness` para futures
que excedem o timeout global, com `pagination_mode=timeout`, `complete=false`,
`pages_fetched=0` e motivo explícito. O erro continua em `errors` e o provider é
classificado como `failed` em `source_outcomes`. Regressão coberta por
`test_client_search_many_reports_timeout_in_source_completeness`.

### Complemento T07

Falhas de provider e timeouts agora repetem `error_type` e `error_message`
sanitizados dentro de `source_completeness`. Os valores sao derivados do mesmo
envelope seguro de `errors`, evitando que consumidores que leem apenas o estado
por fonte percam a classificacao ou confundam falha com fonte nao observada.
O Studio tambem ignora `scope=record` ao construir `source_status`, mantendo a
fonte como `partial` em vez de `failed`. As regressoes de falha, timeout e
quarentena em `tests/test_client_exporters.py` e `tests/test_studio.py` verificam
a paridade do contrato.

| Execução | Resultado |
|---|---|
| `PYTHONPATH=. pytest -q tests/test_client_exporters.py -k search_many` | passed — 12 testes |

| Comando | Resultado |
|---|---|
| `PYTHONPATH=. pytest -q` | passed — 793 testes, 8 skips, 1 aviso existente |
| `python tools/audit_provider_discovery_offline.py` | passed — 55 catalogo, 45 runtime, 9 candidatos, 1 familia; 41 com fixture versionada, 1 somente inline e 3 sem evidencia local |
| `python tools/audit_unified_contract.py` | passed — 41 providers unificados, 4 excluidos por capability declarada |
| `python tools/validate_sdd.py` | passed |

## Rastreabilidade

| Requisito | Evidencia | Estado |
|---|---|---|
| REQ-001 | `NanoJurisClient.search_many`, isolamento por item e testes federados | verified locally |
| REQ-002 | `src/nanojuris/errors.py`, health/validation/collection e testes de seguranca | verified locally |
| REQ-003 | `ResearchRun.record_count`, `persisted_record_count` e testes de storage | verified locally |
| REQ-004 | inventario offline com fixtures versionadas e payload inline separados | verified locally |

## Evidencia adicional de fixtures

Foram extraidas fixtures HTML sanitizadas a partir de payloads inline ja
versionados nos testes: STM, TCE-SP, NugepNac/TJSP, TRE-SP, TJSC/eproc e
TRF4/eproc.
O builder XLSX do STF Informativos permaneceu inline porque representa um
contrato sintetico, nao uma resposta oficial arquivada; nenhuma origem foi
inventada.

Auditoria apos a extracao: 45 providers runtime; 41 com fixture versionada;
1 somente inline; 3 sem fixture ou payload inline. Os testes direcionados dos
seis providers, auditoria e documentacao passaram (33 testes nesta rodada).

## Evidencia live da plataforma

O trace autenticado de producao em `repos/nanojuris-platform/.artifacts/` foi
resumido sem credenciais, cookies, tokens, corpos de resposta ou request IDs em
`docs/validation/runs/20260828T010539Z-platform-live-summary.{json,md}`.
Ele registrou 45 providers no catalogo, 41 pesquisados, 31 com dados, 10 com
falha classificada e 4 ignorados por capability. O assistente retornou HTTP
502, sem resposta ou citacoes. Essa evidência nao altera o status dos adapters
e nao substitui validacao individual das fontes externas.

O mesmo resumo agora inclui um inventario das rotas realmente emitidas pelo
navegador (autenticacao, catalogo, busca/paginacao, assistente e painel
administrativo), com queries redigidas. Novas rodadas devem seguir
`docs/validation/runs/playwright-live-run-template.md`.

## Limites da verificacao

Esta mudanca foi validada offline. A suite nao afirma disponibilidade atual,
alteracoes recentes de HTML, rate limits ou controles de acesso de fontes externas.
