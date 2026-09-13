# Verificação — handoff 0091

Estado deste lote: `locally_verified_with_external_pending` (2026-09-08).
Os gates abaixo demonstram somente consistência local e não equivalem a
disponibilidade permanente, aprovação jurídica ou autorização de release.

## Resultados observados

### TJAL Turmas Recursais (SDD 0095)

O provider `tjal_turma_recursal_ementario` foi incorporado ao runtime como
fonte oficial recursal opt-in. A evidência bounded está em
`docs/provider-discovery/tjal-turma-recursal-live-20260908.json`, com volumes
PDF públicos, escopo `degree=recursal` e `instance=turma_recursal`. A fonte não
é CJPG/CJSG, não oferece voto integral comprovado e mantém `total_unknown`.
Fixtures, contrato, parser, testes e verificação estão no SDD
`specs/changes/0095-tjal-turma-recursal-ementario/`.

| Medida | Resultado | Evidência |
|---|---:|---|
| fontes catalogadas | 71 | `docs/registry/provider-catalog.full.json` |
| providers runtime | 66 | catálogo reconciliado com `docs/registry/providers.json` |
| fontes unificadas declaradas | 49 | resumo do catálogo |
| CJPG comprovados | 7/27 | `docs/topology/degree-coverage-matrix-20260901.json` |
| CJSG comprovados | 25/27 | `docs/topology/degree-coverage-matrix-20260901.json` |
| fixtures runtime completas | 66/66 | `docs/coverage/fixture-completeness-20260908.json` |
| tarefas abertas | 57 | `docs/coverage/open-task-audit-current.json` |
| tarefas locais / externas / humanas | 0 / 44 / 13 | auditoria de tarefas |
| workpacks de superfícies | 150 (125 obrigatórias) | `surface-workpacks/manifest.json` |
| auditoria de artefatos | concluída; marcadores reportados, não apagados | `docs/coverage/0091-artifact-audit-20260908.json` |

Foram feitas chamadas públicas bounded ao endpoint moderno do TJMG e à página
de Informativos do TJMA em `docs/provider-discovery/tjmg-modern-api-live-20260908.json`
e `docs/provider-discovery/tjma-informativos-live-20260908.json`. As evidências
registra busca CJSG de segundo grau, segunda página sem sobreposição, filtro de
classe, detalhe com inteiro teor e `bypass_used=false`. O catálogo passou a
selecionar essa evidência de 2026-09-08, sem editar JSON gerado manualmente.

## Auditoria local executável

```powershell
$env:PYTHONPATH = 'src'
python tools/audit_0091_local_gates.py --write
```

Resultado do lote: **10 gates locais aprovados, 0 pendentes**. O relatório e os
hashes dos artefatos estão em:

- `docs/coverage/0091-local-gates-20260908.json`
- `docs/coverage/0091-local-gates-20260908.md`

O auditor confirma a presença do pacote SDD, reconciliação de 66 providers,
shape do ledger, fixtures, manifesto técnico, referência Juscraper fixada e
evidências TJMG/TJMA. Ele não fecha tarefas que dependem de fonte externa ou
de decisão humana.

## Comandos executados

```text
python tools/audit_open_tasks.py
python tools/build_provider_coverage.py --write
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/build_fixture_completeness.py --write
python tools/validate_sdd.py
python tools/validate_executor_packet.py
python tools/audit_0091_local_gates.py --write
python tools/build_surface_workpacks.py --write
python tools/audit_0091_artifacts.py --write
python tools/build_0091_baseline.py --write
python -m ruff check tools/audit_0091_local_gates.py
python -m ruff format --check tools/audit_0091_local_gates.py
python -m pytest -q
```

Os testes completos passaram: **1578 passed, 26 skipped**. Os skips
são smoke tests live opt-in ou a dependência opcional `lxml`; não representam
falha local.

Nenhum commit, push, tag, publicação, deploy, `terraform apply` ou alteração
de produção foi realizado.

## Rastreabilidade e limites

| Gate | Estado | Motivo |
|---|---|---|
| contrato/runtime local | `verified_local` | catálogo, ledger e runtime reconciliados |
| fixtures | `verified_local` | 66/66 completos no gate local |
| federação técnica | `verified_local` | manifesto técnico presente; promoção legal não inferida |
| live nacional | `pending_external` | 44 tarefas ainda dependem de fontes públicas |
| documentos completos | `partial_external` | detalhe/inteiro teor variam por provider |
| Juscraper/paridade | `partial_external` | referência fixada; equivalência live por provider ainda pendente |
| governança | `pending_human` | 11 decisões humanas aguardam responsável |

CAPTCHA, WAF, Turnstile, 403, 429, TLS, login e schema inválido permanecem
estados explícitos. Não foram convertidos em vazio e não foram contornados.

## Próximo lote recomendado

Executar os providers da ordem 0091 em lotes de um a três, começando pelos
bindings CJSG ainda incompletos. Para cada lote: chamada oficial bounded,
fixture sanitizada, teste de paginação/filtros, smoke federado opt-in e
regeneração dos inventários. Manter as 44 tarefas externas e 13 humanas abertas
até existir evidência ou decisão correspondente.
## Pendência objetiva do benchmark

O benchmark de ranking possui consultas e execução reproduzível. O harness CPU
foi executado para 240 candidatos (p95 62,5 ms, zero chamadas de rede) e o
avaliador foi executado com estado `pending_human_labels` em
`docs/benchmarks/live-ranking-evaluation-20260908.json`. As métricas nDCG@10,
P@5, MRR e irrelevantes@5 não são fabricadas; a aprovação dos rótulos e do
holdout continua em T045.

## Atualização da integração web (2026-09-08)

O fluxo Studio agora envia explicitamente `mode` e `ranking_version` para
`/api/search`. Sem seleção manual de fontes, o navegador usa `mode=adaptive` e
`ranking_version=legal-live-v1`; quando o usuário seleciona fontes, usa
`mode=selected`. A resposta transporta `search_mode`, `ranking_version`,
`query_intent` e o mapa allowlisted de `ranking` por resultado.

No cliente da biblioteca, planos explícitos executam as ondas de fontes em
sequência, respeitando o limite de cada onda e o prazo global. O teste
`tests/test_search_many_ranking.py::test_search_many_executes_explicit_plan_waves_sequentially`
comprova que nenhuma fonte da onda seguinte inicia antes do encerramento da
onda anterior. Isso corrige a execução acidentalmente concorrente que existia
quando o plano declarava três ondas.

Verificações executadas após a mudança:

```text
python -m pytest -q tests/test_studio.py tests/test_search_many_ranking.py
30 passed
python -m ruff check src/nanojuris/client.py src/nanojuris/web/schemas.py src/nanojuris/web/studio.py tests/test_studio.py tests/test_search_many_ranking.py
python -m ruff format --check src/nanojuris/client.py src/nanojuris/web/schemas.py src/nanojuris/web/studio.py tests/test_studio.py tests/test_search_many_ranking.py
cd frontend; npm.cmd run typecheck; npm.cmd run build
```

O ranking continua determinístico, sem LLM, embeddings ou serviço pago. A
calibração humana do benchmark, a renderização final de razões na interface e
qualquer rollout continuam gates separados; não são inferidos a partir de
testes unitários. Nenhum commit, push, deploy ou alteração de produção foi
realizado.

## Rechecagem estadual CJSG (2026-09-08)

Foi executado `python tools/run_cjsg_live_smoke.py --output
docs/provider-discovery/cjsg-live-20260908-cycle67.json --text
"responsabilidade civil" --page-size 1`. O envelope redigido registrou oito
buscas com dados válidos: TJAC, TJAL, TJAM, TJES, TJCE, TJMS, TJPE e TJSP.
Quatro detalhes foram extraídos com sucesso; três responderam com controle de
acesso no detalhe; nenhum bloqueio foi convertido em vazio.

Também foi executado `python tools/run_state_eproc_degree_smoke.py --output
docs/provider-discovery/state-eproc-degree-live-20260908.json`, com um registro
de segundo grau válido para TJRJ e TJSC, HTTP 200 e hashes de resposta. A rota
TJRJ/TJSC continua sem ser contada como CJPG; TJRO permanece separado da fonte
contextual Liame.

Uma sondagem publica limitada adicional, com `degree=first` e `instance=first`,
esta registrada em
`docs/provider-discovery/state-eproc-first-degree-boundary-live-20260908.json`.
TJRJ e TJSC devolveram HTTP 200, mas o parser rejeitou os cards incompatíveis
com `ParserContractChangedError`; nenhum erro foi convertido em vazio. O
payload oficial observado nao expos origem publica distinta de primeiro grau,
portanto as duas superficies continuam CJSG validas e CJPG nao comprovadas.

O lote B2 foi rechecado por `python tools/run_state_cjsg_batch_live.py --output
docs/provider-discovery/state-cjsg-live-20260908-cycle68.json`. TJGO, TJPI,
TJPR, TJRR, TJRS e TJTO retornaram dados em páginas 1 e 2, com seis pares de
IDs disjuntos e `blocked_or_failed=0`. O relatório contém apenas identidades,
estados, hashes e traces redigidos.

O benchmark CPU do ranker foi executado com 50 rodadas e 240 candidatos:
`docs/benchmarks/live-ranking-performance-20260908.json`. O p95 observado foi
62,5 ms, abaixo do limite de 150 ms, com zero chamadas de rede. As métricas de
relevância (nDCG@10, P@5, MRR e irrelevantes@5) continuam corretamente sem
valor até que julgadores humanos preencham development e holdout.

O lote B1 foi rechecado por `python tools/run_state_b1_live.py --output
docs/provider-discovery/state-b1-live-20260908-cycle69.json`. TJBA, TJDFT,
TJMT, TJPA, TJPB e TJRN retornaram duas páginas válidas cada, com identidades
explícitas `degree=second`, sem sobreposição de IDs e sem bloqueio ou falha na
amostra bounded. O artefato preserva somente metadados, hashes e traces; os
corpos das respostas não foram persistidos.

## Evidências live adicionais (2026-09-08)

Foram executados smokes oficiais bounded e de baixa frequência, sem bypass:

| Família | Evidência | Resultado |
|---|---|---|
| STM | `docs/provider-discovery/stm-live-20260908-cycle70.json` | busca, paginação e detalhe válidos; 0 erros |
| TRF4 | `docs/provider-discovery/trf4-live-20260908-cycle71.json` | busca, paginação e detalhe válidos; 0 erros |
| TRF5 | `docs/provider-discovery/trf5-live-20260908-cycle72.json` | busca, paginação e detalhe válidos; 0 erros |
| eproc | `docs/provider-discovery/eproc-detail-live-20260908-cycle73.json` | 3 detalhes válidos; 0 erros de detalhe |

Essas chamadas acrescentam evidência de disponibilidade das amostras, mas não
fecham automaticamente os contratos nacionais, a completude de documentos, a
paridade por provider ou as decisões humanas de licença/retenção.

## Sondagens adicionais e correções técnicas

As sondagens de primeiro grau em TJBA e TJPA foram preservadas sem automação de
desafio. TJBA expôs formulário público de Banco de Sentenças, mas o POST
respondeu exigindo CAPTCHA; TJPA declarou acesso restrito a magistrados. O
resultado consolidado está em
`docs/provider-discovery/first-degree-secondary-probes-live-20260907.json` e
esses estados permanecem `blocked_access`, não vazio.

A paginação recebeu uma guarda de consistência para o caso em que a fonte
declara `total_known=true` e `total=0` enquanto entrega registros. O coletor
preserva os registros, marca `inconsistent_total` e não afirma completude. Os
testes de regressão em `tests/test_pagination.py` e `tests/test_collection.py`
passaram.

Os contratos de TJSP/NugepNac, STF, CJF, TJCE e TJAP foram alinhados aos campos
canônicos efetivamente produzidos pelos parsers; os scorecards e inventários
foram regenerados. A mudança não altera estados de acesso nem concede promoção
automática a fontes bloqueadas.

O provider TJRJ Banco de Sentenças também foi rechecado. O índice PDF respondeu
200 e foi preservado; o primeiro documento individual permaneceu 503 e foi
classificado como `source_unavailable`, sem retry agressivo ou bypass. A tarefa
técnica correspondente foi fechada, mas a decisão humana de promoção continua
pendente em T0090.

O contrato comum eproc federal foi fechado tecnicamente em T023. A execução
bounded de `tools/run_eproc_detail_smoke.py` comprovou identidade de segundo
grau e detalhe textual para TNU, TRF2 e TRF6 no artefato
`docs/provider-discovery/eproc-detail-live-20260908-cycle75.json`. Isso não
encerra outras lacunas federais nem decisões humanas de governança.

### Evidencia TJRO de inteiro teor (2026-09-08)

Uma chamada publica bounded de `tjro_jurisprudencia` confirmou um registro
PJESG de segundo grau e seu documento PDF. O MIME foi `application/pdf`, o
documento tinha 29.618 bytes e o texto extraido 11.949 caracteres; hash
`ed3c357720fd7744dfd0f6f79a35d000ae89e45efb6957744dfd0f6f86b80a0`.
Registro redigido: `docs/provider-discovery/tjro-jurisprudencia-fulltext-live-20260908.json`.
Isso apenas reforca a capacidade de inteiro teor do provider; nao e aprovacao
legal nem declaracao de cobertura nacional.

### Rechecagem TRF3 por identificador exato (2026-09-08)

Foi feita uma tentativa pública e limitada contra a rota oficial de
`trf3_jurisprudencia`, usando o processo CNJ conhecido
`00079799120054036119`, com limite de 20 segundos e sem credenciais, solver ou
contorno de proteção. A tentativa terminou em `source_unavailable` por timeout
de leitura HTTPS (`20676.71 ms`). Nenhum corpo foi persistido e o resultado não
foi convertido em vazio. A evidência redigida está em
`docs/provider-discovery/trf3-exact-process-live-20260908.json`; o provider
o provider permanece `opt_in_pending_live` e a tarefa externa T0087 continua aberta.

### Atualização do handoff: TJAC (SDD 0094)

O provider `tjac_ementario_jurisprudencia` foi incorporado ao runtime como uma
coleção oficial de ementário de segundo grau, sem alegar cobertura integral do
tribunal. A evidência bounded está em
`docs/provider-discovery/tjac-ementario-live-20260908.json`: HTTP 200,
`application/pdf`, 593570 bytes, sete registros para `constitucional`,
`degree=second`, `instance=second`, `branch=state` e sem bypass. O parser
recompõe blocos de cabeçalho/ementa que atravessam páginas, aplica filtros
locais sobre a janela do PDF e declara `total_unknown`/`is_complete=false`.

Arquivos do lote: `src/nanojuris/providers/tjac_ementario_jurisprudencia.py`,
fixtures e `tests/test_tjac_ementario_jurisprudencia.py`, dossiê/contrato em
`docs/providers/tjac_ementario_jurisprudencia/` e
`docs/source-contracts/tjac_ementario_jurisprudencia.md`, e SDD
`specs/changes/0094-tjac-ementario-jurisprudencia/`. Os cinco testes focados
passaram; o fechamento posterior registrou 1578 testes aprovados e 26 skips.
Esta fonte é parcial e não fecha nenhuma lacuna CJPG/CJSG nacional sozinha.
