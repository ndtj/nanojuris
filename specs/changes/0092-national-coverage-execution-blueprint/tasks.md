# Tarefas — blueprint de execução

Legenda: `[L]` local, `[E]` depende de fonte externa, `[H]` depende de decisão
humana. Todas começam pendentes para o próximo modelo; marcar `[x]` somente
com evidência no `verification.md` correspondente.

## Baseline

- [x] **T001 [L]** ler AGENTS, constituição, SDD 0091 e dossiê do provider.
- [x] **T002 [L]** regenerar todos os inventários e salvar hash do baseline.
- [x] **T003 [L]** reconciliar runtime, catálogo, live, qualidade e federação.
- [x] **T004 [L]** identificar superfícies sem registro canônico ou evidence ID.

## Contratos

- [x] **T005 [L]** fechar estados de total e acesso no envelope federado.
- [x] **T006 [L]** validar grau, instância, ramo, coleção e tipo por registro.
- [x] **T007 [L]** fechar matriz de filtros remotos, traduzidos, locais e ignorados.
- [x] **T008 [L]** validar paginação, cursor, ordenação e sobreposição.
- [x] **T009 [L]** validar datas, granularidade, timezone e ausência.
- [x] **T010 [L]** fechar DocumentReference, extração e provenance.

## Descoberta e providers

- [ ] **T011 [E]** confirmar fonte oficial e rota pública por superfície CJPG.
- [ ] **T012 [E]** confirmar fonte oficial e rota pública por superfície CJSG.
- [ ] **T013 [E]** fechar TRF/STJ/STF/STM/CJF com contratos documentais.
- [ ] **T014 [E]** fechar TRT/TST e TSE/TRE/SJUR sem misturar coleções.
- [x] **T015 [L]** comparar Juscraper por contrato, sem copiar implementação.
- [ ] **T016 [E]** executar chamadas bounded e classificar bloqueios.

## Adapters e fixtures

- [x] **T017 [L]** implementar parser independente somente para rota reproduzível.
- [ ] **T018 [E]** registrar fixture sanitizada de sucesso e segunda página.
- [ ] **T019 [E]** registrar vazio autoritativo e vazio não confirmado separados.
- [x] **T020 [L]** registrar parâmetro inválido, schema drift e erro externo.
- [ ] **T021 [E]** validar detalhe, PDF/HTML, MIME, hash e limites.
- [x] **T022 [L]** testar identidade canônica e deduplicação.

## Federação e qualidade

- [x] **T023 [L]** executar smoke opt-in sem alterar rollout padrão.
- [x] **T024 [L]** promover somente com oito gates válidos.
- [x] **T025 [L]** validar planner, filtros, completude e diagnósticos.
- [x] **T026 [L]** validar ranking determinístico e razões de relevância.
- [ ] **T027 [H]** aprovar rótulos de benchmark e holdout.

## Operação e governança

- [x] **T028 [L]** configurar TTL, smoke periódico, drift, métricas e rollback.
- [ ] **T029 [H]** aprovar licença, retenção, frequência e responsável.
- [ ] **T030 [H]** autorizar promoção padrão, release ou mudança externa.
- [x] **T031 [L]** gerar relatório final com lacunas e próxima ação.

## Decisões fixadas em 2026-09-09

Os valores normativos são 2 segundos entre requisições por provider, no máximo
três páginas por sonda, cache de 600 segundos e telemetria de 30 dias. T027,
T029 e T030 continuam dependentes do mantenedor; pré-rótulos não simulam
aprovação humana.

## Dependências

`T001–T004 → T005–T010 → T011–T016 → T017–T022 → T023–T026 →
T027–T031`. T027, T029 e T030 nunca podem ser simuladas pelo executor.
