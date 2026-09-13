# Tarefas — busca live inteligente e determinística

Referência: `specs/changes/0077-live-intelligent-federated-search/spec.md`

Todos os itens de implementação começam pendentes. Marcar como concluído apenas
com teste/evidência em `verification.md`.

## Preparação

- [x] **T01** — auditar ranking, routing, contrato web e merge atuais.
- [x] **T02** — registrar decisões de produto, alternativas e baseline live.
- [x] **T03** — criar pacote SDD completo e validar sua consistência.
- [x] **T04** — capturar/reconstruir baseline imutável de testes e payloads
  offline antes de novas alterações.

## Intenção jurídica — REQ-001 a REQ-005

- [x] **T05** — criar `QueryIntent`, `LegalConceptMatch` e versão do analisador.
- [x] **T06** — implementar normalização Unicode/acento/casefold determinística.
- [x] **T07** — reconhecer número CNJ e identificadores antes da tokenização.
- [x] **T08** — implementar stopwords ponderadas e termos de comando.
- [x] **T09** — implementar aspas, frases compostas e proximidade preparatória.
- [x] **T10** — implementar termos obrigatórios, opcionais e negativos.
- [x] **T11** — criar léxico jurídico v1 com schema, IDs e pesos limitados.
- [x] **T12** — detectar filtros inequívocos e separar sugestões ambíguas.
- [x] **T13** — adicionar testes dourados, incluindo as seis queries obrigatórias.

## Roteamento e query plan — REQ-006 a REQ-009

- [x] **T14** — criar modelos `SearchMode`, `SearchPlan`, `SourceWave` e
  `ProviderQueryPlan`.
- [x] **T15** — implementar score de elegibilidade a partir de capabilities.
- [x] **T16** — implementar exclusão de blocked/contextual inadequado.
- [x] **T17** — implementar diversidade de autoridade e seleção 8–12.
- [x] **T18** — implementar formação estável das três ondas.
- [x] **T19** — implementar orçamento máximo de 240 e 15–20 por fonte.
- [x] **T20** — compilar filtros native/translated/local/unsupported.
- [x] **T21** — integrar planner ao router 0038 sem duplicar regras.
- [x] **T22** — testar adaptive, selected, all, opt-in, identifiers e desempates.

## Estados e execução — REQ-008 a REQ-011

- [x] **T23** — criar enum/modelo dos dez outcomes v2.
- [x] **T24** — mapear sucesso, vazio provado e vazio não confirmado.
- [x] **T25** — mapear timeout, bloqueio, rate limit, transporte e schema drift.
- [x] **T26** — mapear parcial, truncamento e cancelamento.
- [x] **T27** — medir latência e páginas por fonte sem registrar conteúdo.
- [x] **T28** — impor uma chamada normal por provider e deadlines especificados.
- [x] **T29** — testar que 403/429/CAPTCHA/TLS/parser nunca viram vazio.

## Ranking — REQ-012 a REQ-018

- [x] **T30** — criar projeção allowlisted e limitada dos campos ranqueáveis.
- [x] **T31** — implementar cobertura com pesos estáticos versionados e
  independentes da onda.
- [x] **T32** — implementar frase exata por campo e proximidade.
- [x] **T33** — implementar cobertura de conceitos e expansões com teto 0,4.
- [x] **T34** — implementar consistência de filtros e qualidade documental.
- [x] **T35** — implementar RRF do rank nativo com constante 20.
- [x] **T36** — implementar penalidades e rejeição de conflitos explícitos.
- [x] **T37** — implementar match CNJ com score mínimo 99,9.
- [x] **T38** — implementar desempate estável e score público de uma casa.
- [x] **T39** — gerar até três razões allowlisted e comprováveis.
- [x] **T40** — integrar ranker v1 ao `search_many` atrás de flag.
- [x] **T41** — testar monotonicidade, permutação, NaN, vazio e limites.

## Identidade e diversidade — REQ-016 e REQ-017

- [x] **T42** — preservar deduplicação canônica e CNJ cross-source existente.
- [x] **T43** — implementar equivalência de documento e fingerprint textual.
- [x] **T44** — impedir fusão de retificação, republicação ou versão distinta.
- [x] **T45** — expor grupo e fontes duplicadas sem raw.
- [x] **T46** — implementar diversidade somente em near-ties e testar limites.

## API e compatibilidade — REQ-018, REQ-022, REQ-025 e REQ-026

- [x] **T47** — estender request/response da lib de forma aditiva.
- [x] **T48** — estender Pydantic, serviço e OCI Function com contratos idênticos.
- [x] **T49** — atualizar projeções browser/research por allowlist.
- [x] **T50** — versionar chave/TTL de cache sem criar corpus pesquisável.
- [x] **T51** — testar payload legado, versão inválida, limites e redaction.
- [x] **T52** — adicionar gate que proíbe dependências/chamadas de IA e vetor.

## Plataforma web — REQ-019 a REQ-021

- [x] **T53** — implementar execução progressiva por ondas e geração de busca.
- [x] **T54** — substituir concatenação por merge global ranqueado.
- [x] **T55** — preservar seleção, reader, paginação e filtro visual por ID.
- [x] **T56** — implementar freeze por interação e buffer de ranking pendente.
- [x] **T57** — implementar ação "Aplicar resultados mais relevantes".
- [x] **T58** — renderizar chips removíveis, razões e estados de fonte.
- [x] **T59** — implementar acessibilidade, reduced motion e anúncio moderado.
- [x] **T60** — testar ondas fora de ordem, cancelamento, freeze e nova geração.

## Benchmark, operação e fechamento — REQ-023 e REQ-024

- [x] **T61** — criar dataset, schema, guia de julgamento e métricas offline.
- [ ] **T62** — medir/calibrar development, validar holdout e performance p95.
- [x] **T63** — implementar legacy/shadow/v1, telemetria mínima e rollback local.
- [x] **T64** — executar suíte completa, smokes bounded, SDD e fechar evidências.

## Dependências

```text
T01-T04
  -> T05-T13
  -> T14-T22
  -> T23-T29
  -> T30-T41
  -> T42-T46
  -> T47-T52
  -> T53-T60
  -> T61-T64
```

T30–T41 podem começar após T13; T23–T29 podem avançar junto de T14–T22. A
integração API/web só começa quando tipos e score estiverem testados.

## Condição de conclusão

- T04–T64 concluídas ou justificadamente descartadas.
- AC-001–AC-024 com evidência.
- Nenhuma regressão nos dois repositórios.
- Nenhum commit, push, publicação ou deploy.

## Decisões fixadas em 2026-09-09

Aplicar `docs/coverage/decision-record-20260909.json`: shadow mode permanece
ativo; telemetria retém somente fingerprint HMAC por 30 dias; cache live tem
TTL de 10 minutos; o benchmark exige revisão humana das 80 linhas (8 x top
10). Pré-rótulos não encerram T62.
