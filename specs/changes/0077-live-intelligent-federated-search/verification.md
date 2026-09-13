# Verificação — busca live inteligente

Referência: `specs/changes/0077-live-intelligent-federated-search/spec.md`
Status: `implementation_locally_verified; human relevance calibration pending`

## Ambiente

- Workspace: `C:\Users\admin\Desktop\Nanojuris`
- Repositórios: `repos/nanojuris`, `repos/nanojuris-platform`
- Data do planejamento: `2026-09-07`
- Worktrees: possuem alterações anteriores legítimas; devem ser preservadas.

## Evidência já obtida

- O cliente atual ranqueia por contagem simples de tokens em poucos campos.
- O merge web atual concatena lotes sem reranking global.
- A API limita uma chamada a 12 fontes.
- O default atual usa três fontes recomendadas.
- Chamadas bounded das queries de referência mostraram bons documentos e falsos
  positivos no mesmo top, justificando o benchmark.
- O SDD 0038 já entrega filtros/outcomes/completude básicos e proíbe comparar
  scores remotos; este pacote estende essa base.

## Comandos de baseline a executar

```powershell
cd C:\Users\admin\Desktop\Nanojuris\repos\nanojuris
python tools/validate_sdd.py
python -m pytest -q tests/test_client_exporters.py tests/test_provider_contract_v2.py tests/test_routing.py
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check

cd C:\Users\admin\Desktop\Nanojuris\repos\nanojuris-platform
python -m pytest -q tests/test_function.py tests/test_guardrails.py tests/test_browser_session.py
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tests
git diff --check
```

Se algum nome focado não existir, localizar o teste equivalente com `rg --files
tests` e registrar a substituição; não ocultar o desvio.

## Comandos de fechamento

```powershell
cd C:\Users\admin\Desktop\Nanojuris\repos\nanojuris
python tools/validate_sdd.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check

cd C:\Users\admin\Desktop\Nanojuris\repos\nanojuris-platform
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tests
git diff --check
```

## Resultados

- T05–T13 concluídas localmente com `src/nanojuris/search_intent.py` e o
  vocabulário versionado `src/nanojuris/data/legal-vocabulary-v1.json`.
- Testes focados: `python -m pytest -q tests/test_search_intent.py` — 10 passed.
- Ruff, formatação e mypy do analisador — aprovados.
- O analisador reconhece CNJ, filtros explícitos, tipos documentais,
  conceitos compostos, termos negativos e ambiguidades de autoridade sem rede.
- T30–T34 e T36–T39 implementadas em `src/nanojuris/relevance.py` com campos
  allowlisted, cobertura lexical, frases, conceitos, penalidades, match CNJ,
  desempate estável e razões explicáveis.
- T35 implementada com `reciprocal_rank_fusion` e constante `RRF_K=20`; o teste
  confirma deduplicação de posições dentro da mesma variante.
- Testes focados do ranker: `python -m pytest -q tests/test_relevance.py` — 5
  passed.
- Testes focados do ranker: `python -m pytest -q tests/test_relevance.py` — 4
  passed. Ruff, formatação e mypy — aprovados.
- T35 (RRF entre variantes) permanece limitada à API primitiva; T40 foi concluída com integração
  opt-in em `search_many` e `search_many_and_store_run`. Sem `ranking_version`,
  o payload e a ordenação legados permanecem inalterados.
- Testes de integração do ranking: `python -m pytest -q
  tests/test_search_many_ranking.py tests/test_client_exporters.py` — 48 passed.
- T40 expõe apenas metadados allowlisted (`ranking`, `query_intent` e
  `ranking_complete`) e não serializa resposta raw, headers ou cookies.

| Gate | Estado | Evidência requerida |
| --- | --- | --- |
| SDD completo | pass nesta fase | arquivos do pacote e validador |
| Intenção | pending | golden queries e AC-001/002 |
| Planner | pending | 8–12 fontes, ondas e plans snapshot |
| Outcomes | pending | matriz de falhas AC-005/006 |
| Ranking | pending | testes determinísticos e razões |
| Benchmark | pending | nDCG/P@5/MRR/irrelevante@5 |
| Performance | pending | relatório p50/p95 de 240 candidatos |
| API/compatibilidade | pending | lib/FastAPI/Function e payload legado |
| UX/a11y | pending | browser acceptance e Playwright |
| Segurança | pending | threat model e redaction tests |
| Suíte completa | pending | comandos de fechamento |
| Live bounded | pending | queries obrigatórias por fontes selecionadas |

## Evidência adicional do planner

T14–T22 foram concluídas com `src/nanojuris/adaptive_search.py`: modos
`adaptive`, `selected` e `all`, score determinístico de elegibilidade,
exclusão de fontes sem contrato público, diversidade por autoridade, três ondas
estáveis, limites de 12 fontes/240 candidatos e planos de filtros derivados de
`plan_federated_query`.

Testes do planner e integração:
`python -m pytest -q tests/test_adaptive_search.py tests/test_search_many_ranking.py
tests/test_federated_filter_envelope.py tests/test_provider_contract_v2.py` —
33 passed.

`NanoJurisClient.search_many(mode="adaptive")` é opt-in, usa ranking v1 por
padrão nesse modo, limita candidatos por fonte e expõe `search_plan`; sem
`mode`, o comportamento legado permanece inalterado.

T23–T29 foram concluídas com `SearchOutcomeStatus`, `SearchSourceOutcome`,
`search_outcome_from_page` e `search_outcome_from_error` em
`src/nanojuris/contracts.py`. A resposta opt-in inclui `source_outcomes_v2` com
latência, páginas, contagem, estado do total e filtros, sem conteúdo raw.
Testes cobrem vazio autoritativo versus desconhecido, parcial, timeout,
bloqueio, schema e transporte; falhas nunca são classificadas como vazio.

T42–T46 foram concluídas em `federated.py` e `relevance.py`. A fusão mantém a
identidade canônica e CNJ, adiciona equivalência conservadora por URL/texto
normalizado, preserva republicações/retificações, expõe `duplicate_groups` sem
raw e aplica diversidade apenas dentro de uma margem de relevância configurável.
Testes: `tests/test_federated_equivalence.py` e a suíte federada — aprovados.

## Protocolo de benchmark

1. Separar `development` e `holdout` antes de calibrar pesos.
2. Gerar pool unido do ranking legado, novo e ranks nativos.
3. Ocultar score/algoritmo do julgador.
4. Julgar 0–3 usando guia fixo.
5. Resolver divergência de dois julgadores por terceiro julgamento quando
   diferença >= 2.
6. Calibrar somente development.
7. Medir holdout uma vez para gate final.
8. Publicar apenas métricas agregadas e IDs públicos dos casos.

## Smokes obrigatórios

- `responsabilidade civil administrativa`;
- `acórdãos sobre divórcio`;
- `dano moral inscrição indevida`;
- `servidor público acumulação de cargos`;
- `prisão preventiva contemporaneidade`;
- número CNJ público conhecido e sanitizado.

Cada smoke deve registrar fontes planejadas, outcomes, latências, top 10 e
classificação humana, sem guardar headers/cookies ou payload raw.

## Rastreabilidade

REQ-001–REQ-026 estão ligados a AC-001–AC-024 e T05–T64 em
`traceability.md`. T01–T03 comprovam somente a preparação; não fecham nenhum
critério funcional.

## Divergências e riscos residuais

- Toda implementação está pendente por solicitação expressa do usuário.
- Não há autorização de commit, push ou deploy.
- A meta quantitativa pode exigir calibração, mas não autoriza IA ou índice.

## Decisão

- [x] Planejamento aprovado para execução por outro modelo.
- [ ] Implementação verificada.
- [ ] Aprovado para merge.
- [ ] Aprovado para release.

## Fechamento técnico T47–T60 (execução local)

- T47–T48: `NanoJurisClient.search_many` e `search_many_and_store_run` aceitam
  `mode`/`ranking_version` de forma aditiva; a API Pydantic, o serviço e a
  Function validam o mesmo conjunto (`adaptive`, `selected`, `all`, `legacy`;
  `legal-live-v1`/`legacy`). Testes de guardrails e Function: 49 passed.
- T49/T54/T55: a projeção web utiliza somente campos allowlisted, carrega
  `query_intent`, `source_outcomes_v2` e `ranking`, faz merge determinístico
  entre lotes e mantém seleção, leitor, paginação e filtro visual por identidade.
- T50: `TransportRequest.cache_version` participa do SHA-256 da chave; o
  `ContentResponseCache` continua efêmero, limitado por TTL/bytes e sem busca
  sobre o conteúdo. Testes confirmam namespaces distintos e limites.
- T51/T52: payload legado e versões inválidas permanecem cobertos; o gate
  `tools/audit_search_no_ai.py --json` passou sem violações em 144 arquivos.
  Nenhum import/call de LLM, embeddings, vetor ou reranking pago é aceito no
  runtime da busca.
- T53/T56/T57/T60: o navegador usa ondas 3/4/rest para listas explicitamente
  selecionadas, sinaliza progresso, congela a ordem após foco/seleção/rolagem,
  mantém um buffer e oferece “Aplicar ordem”; cancelamento mantém os resultados
  já recebidos. O contrato estático é verificado em
  `nanojuris-platform/tests/test_search_ui_contract.py`.
- T58/T59: chips de intenção podem remover inferências numa nova consulta;
  razões allowlisted e estados de fonte são renderizados com `aria-live` e o
  CSS existente respeita `prefers-reduced-motion`.

Comandos focados:

```text
python -m pytest -q tests/test_transport_runtime.py tests/test_search_no_ai.py tests/test_search_intent.py tests/test_adaptive_search.py tests/test_search_many_ranking.py tests/test_search_outcomes.py tests/test_federated_equivalence.py
python tools/audit_search_no_ai.py --json
```

Resultado: 31 testes focados da biblioteca passaram; o gate sem IA passou.
Ainda faltam T04, a calibração/holdout de T62 e T64 (suíte completa, smokes
bounded e fechamento de todos os gates); esses itens não podem ser declarados
concluídos sem dados de julgamento humano e execução final.

### Evidência adicional T61–T63

- T61: `docs/benchmarks/live-ranking-v1.json`, seu schema e guia de julgamento
  registram as oito consultas sanitizadas, os splits development/holdout, a
  escala 0–3 e o estado explícito `pending_human_labels`. O avaliador
  `tools/evaluate_live_ranking.py` não inventa métricas quando não há rótulos.
- T62: o benchmark local de CPU para 240 candidatos foi executado com 25
  rodadas; p95 observado 56,444 ms em
  `docs/benchmarks/live-ranking-performance-20260907.json`, abaixo do orçamento
  de 150 ms. Calibração e holdout continuam pendentes de julgamentos humanos.
- T63: `legacy`, `legal-live-v1` e o shadow bounded existentes são reversíveis;
  `search_telemetry.py` expõe apenas HMAC da consulta, posição, provider,
  identificador canônico e latência, com `raw_query=None` e retenção definida
  na política do benchmark.

### Medição adicional de performance T62

Uma segunda execução de 1.000 rodadas para 240 candidatos observou p95 de
78,125 ms de CPU em `docs/benchmarks/live-ranking-performance-20260907-cycle2.json`,
abaixo do limite de 150 ms, com zero chamadas de rede. O benchmark mede tempo
de processo para não confundir pausas do agendador do sistema com regressão do
ranker. Os rótulos humanos, a calibração e o holdout continuam pendentes por
desenho.

### Fechamento local T64

- A suíte completa da biblioteca passou: `1504 passed, 26 skipped` em
  (`python -m pytest -q`). Os skips são exclusivamente testes live
  opt-in e a dependência opcional `lxml`.
- Os gates locais passaram novamente: `validate_sdd`, Ruff, formatação, mypy,
  `compileall` e `git diff --check`.
- O smoke federado histórico de 42 fontes permanece disponível em
  `docs/provider-discovery/federated-promotion-live-20260906-current.json`;
  ele mantém erros externos explícitos. Um novo smoke bounded executou as seis
  consultas do benchmark contra `cnj_jurisprudencia` e gravou somente hashes,
  estados, latências e contagens em
  `docs/benchmarks/live-ranking-smoke-20260907.json`; nenhum corpo, cookie ou
  cabeçalho foi persistido.
- T64 está concluída localmente. T62 (rótulos humanos, calibração e holdout)
  continua deliberadamente pendente; não é substituído por dados sintéticos.

### Rechecagem tecnica T62 em 2026-09-08

Uma nova execucao de 1.000 rodadas para 240 candidatos observou mediana de
15,625 ms, p95 de 46,875 ms e maximo de 78,125 ms, com zero chamadas de rede.
O artefato esta em `docs/benchmarks/live-ranking-performance-20260908-rerun.json`.
O gate tecnico de performance permanece abaixo de 150 ms; rotulos humanos,
calibracao no development e validacao do holdout continuam pendentes e nao
sao substituidos por dados sinteticos.

### Componente BM25 (`bm25-v1`) - 2026-09-11

- `BM25Scorer` foi implementado como pontuador fieldado de lote, com `k1=1.2`,
  `b=0.75`, IDF suavizado, limites por campo e normalizacao `[0,1]`.
- O calculo usa somente candidatos live materializados; nao cria indice, nao
  persiste corpus e nao faz chamadas de IA ou rede.
- `LegalLiveRanker` incorpora o sinal BM25 com peso 0,10 e a API anota
  `bm25_score`/`bm25_version` em cada item ranqueado. O envelope tambem
  expoe `bm25_version` quando `legal-live-v1` esta ativo, inclusive quando
  a coleta nao retorna candidatos.
- Testes cobrem limite, determinismo por permutacao e exposicao da anotacao. A
  suite completa final passou com 1.757 testes aprovados e 26 skips opt-in.
- Benchmark bounded de 100 rodadas com 240 candidatos: p95 de 46,875 ms, sem
  chamadas de rede; evidencia em
  `docs/benchmarks/live-ranking-performance-20260911-bm25.json`.

### Baseline T04

- `tools/capture_search_baseline.py` reconstrói o estado pre-change a partir do
  commit imutável `b20b874960d6a856d4812ab52a966d919aaa773b` e registra hashes
  dos contratos e 77 fixtures em
  `docs/benchmarks/live-ranking-baseline-20260907.json`.
- Nenhum payload bruto é persistido. O baseline é uma reconstrução da revisão
  anterior disponível na worktree, não uma alegação de que o modelo atual foi
  executado naquele instante.
