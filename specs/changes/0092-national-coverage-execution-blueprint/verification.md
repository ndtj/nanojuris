# Verificação do blueprint

Status: `locally_verified_with_external_pending` — este pacote cria planejamento
e templates e teve seus artefatos locais validados; não afirma que os providers
foram todos alterados ou que a cobertura nacional foi concluída.

## Resultados

Os gates do blueprint foram validados localmente; a execução de providers ainda
é responsabilidade do próximo modelo. Ele deve registrar aqui a data, o comando,
o código de saída e o artefato produzido para cada lote. Nenhuma evidência local
é tratada como chamada live de uma fonte externa.

## Verificações necessárias pelo próximo modelo

```powershell
$env:PYTHONPATH='src'
python tools/validate_sdd.py
python tools/audit_provider_docs.py --write
python tools/build_provider_coverage.py --write
python tools/build_provider_quality.py --write
python tools/build_provider_capability_ledger.py --write
python tools/build_fixture_completeness.py --write
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

## Evidência esperada

Para cada lote, anexar no SDD do provider: arquivos alterados, chamadas live
bounded, classificação, fixtures, testes focados, contagens regeneradas,
limitações externas e decisão de promoção. Nenhuma linha “passou” sem comando
ou artefato correspondente.

## Limitações conhecidas

- desafios externos e decisões de licença continuam fora do controle do modelo;
- o baseline deve ser regenerado porque os inventários são gerados;
- 27/27 somente pode ser declarado se o programa nacional confirmar os oito
  gates para cada autoridade;
- nenhum commit, push, deploy ou produção foi executado por este blueprint.

## Validação do pacote de handoff

Os artefatos foram validados localmente em 2026-09-08: `python tools/validate_sdd.py`
passou; a suíte local passou com 1566 testes e 26 skips; Ruff, formatação, mypy,
compilação e `git diff --check`
passaram. Essa validação comprova a consistência do pacote, não encerra as
tarefas operacionais `[L]`, `[E]` ou `[H]` acima.

## Rastreabilidade

| Requisito | Tarefa | Resultado esperado |
| --- | --- | --- |
| REQ-092-001–003 | T001–T004 | baseline e registro regenerados |
| REQ-092-004–006 | T005–T009 | contratos e filtros verificáveis |
| REQ-092-007–009 | T010, T018–T021 | documentos e fixtures auditáveis |
| REQ-092-010–011 | T015–T016 | diff Juscraper e live bounded |
| REQ-092-012–014 | T017, T022–T026 | smoke e promoção técnica |
| REQ-092-015–016 | T016, T028–T030 | matriz de acesso e revisão |

## Fechamento local do blueprint

### Evidencia adicional TJRO (2026-09-08)

Foi executada uma chamada live publica e limitada de `tjro_jurisprudencia`
com `degree=second`, `instance=second` e `fetch_details=True`. A busca respondeu
HTTP 200 com um registro PJESG; o PDF de inteiro teor respondeu
`application/pdf`, 29.618 bytes, com 11.949 caracteres extraidos. O hash do
documento e `ed3c357720fd7744dfd0f6f79a35d000ae89e45efb6957744dfd0f6f86b80a0`.
A prova redigida esta em
`docs/provider-discovery/tjro-jurisprudencia-fulltext-live-20260908.json`.
Nenhum corpo bruto foi persistido, e nenhum gate de federacao ou aprovacao
humana foi alterado por essa evidencia isolada.

As tarefas locais T001–T010, T015, T017, T020, T022–T026, T028 e T031 foram
marcadas como concluídas somente após os artefatos abaixo serem regenerados e
verificados:

- `docs/registry/provider-catalog.full.json` e `docs/coverage/provider-capability-ledger.json`;
- `docs/coverage/surface-state-registry-20260902.json` e
  `docs/coverage/state-appellate-program-20260905.json`;
- `docs/coverage/fixture-completeness-20260908.json` (64/64 runtime);
- `docs/coverage/open-task-audit-current.json` (nenhuma tarefa `local_evidence`);
- testes de contratos, filtros, paginação, identidade, deduplicação, ranking,
  promoção e telemetria;
- `python tools/validate_sdd.py`, Ruff, formatação, mypy, compilação e suíte
  completa local.

As tarefas T011–T014, T016, T018–T019 e T021 permanecem externas porque
dependem de respostas públicas dos tribunais. T027, T029 e T030 permanecem
humanas por exigirem rótulos, retenção, responsável ou autorização de rollout.
