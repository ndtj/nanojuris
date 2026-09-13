# Design — busca live inteligente e determinística

Referência: `specs/changes/0077-live-intelligent-federated-search/spec.md`

## Decisão arquitetural

Implementar um pipeline CPU-only sobre a janela live retornada pelos providers.
O núcleo ficará em `nanojuris` e a plataforma consumirá envelopes aditivos. A
API não manterá corpus, vetor ou índice. A qualidade virá de interpretação
jurídica determinística, roteamento por capabilities, pontuação comparável,
fusão de rank nativo e deduplicação.

O SDD 0038 continua responsável pela honestidade semântica da federação. O 0077
introduz o ranking por relevância que 0038 condicionou a benchmark e opt-in.

## Componentes

```text
Web SearchForm
  -> SearchRequest(mode, query, explicit filters)
  -> LegalQueryAnalyzer
       -> QueryIntent
  -> AdaptiveSourcePlanner
       -> SearchPlan + SourceWave[1..3]
  -> ProviderQueryCompiler
       -> ProviderQueryPlan[]
  -> bounded NanoJurisClient.search_many per wave
       -> SourceOutcome[] + canonical candidates
  -> LegalLiveRanker
       -> scored candidates
       -> exact/near deduplication
       -> near-tie diversity
  -> browser projection
       -> progressive merge by ranking score
  -> freeze controller after user interaction
```

## Módulos propostos

Na biblioteca:

- `nanojuris.search_intent`: análise, normalização e vocabulário.
- `nanojuris.live_search`: modelos `SearchMode`, `SearchPlan`, ondas e outcomes.
- `nanojuris.relevance`: extração de sinais, score, RRF, deduplicação e razões.
- `nanojuris.routing`: extensão do router atual para seleção adaptativa.
- `NanoJurisClient.search_many`: integração compatível e metadados do ranking.

Na plataforma:

- `service.py`: validação de modo, execução/projeção e proteção de limites.
- `function.py` e `api.py`: contratos aditivos idênticos.
- `web/app.js`: ondas, merge por score, freeze e chips.
- CSS existente: estados de progresso, reasons e atualização pendente.

O executor deve preferir arquivos coesos e não criar uma classe por regra.

## Modelo de intenção

`QueryIntent` será dataclass serializável:

```text
original_query: str
normalized_query: str
normalized_terms: tuple[str, ...]
phrases: tuple[str, ...]
required_terms: tuple[str, ...]
optional_terms: tuple[str, ...]
excluded_terms: tuple[str, ...]
legal_concepts: tuple[LegalConceptMatch, ...]
detected_filters: dict[str, str]
suggested_filters: dict[str, str]
ambiguous_interpretations: tuple[str, ...]
is_exact_identifier: bool
analyzer_version: str
```

### Normalização

- aplicar NFKD, remover marcas combinantes e `casefold` para comparação;
- manter letras/números e reconhecer CNJ antes de remover pontuação;
- preservar valores originais para UI e envio ao provider;
- stopwords não somam score, mas continuam na consulta remota se removê-las
  puder alterar a semântica do provider;
- tokens com dois caracteres são preservados somente se estiverem no léxico
  jurídico (`ir`, `ip`, por exemplo); demais exigem três caracteres;
- negação aceita prefixo `-termo` e campo `without_words` existente;
- aspas formam frase explícita; conceitos curados podem formar frases
  implícitas.

### Léxico v1

Arquivo de dados versionado, sem código executável, contendo:

- termos de comando: acórdão, decisão, sentença, jurisprudência, precedente;
- tipos documentais e variantes ortográficas;
- graus e instâncias;
- ramos e tribunais;
- conceitos compostos e sinônimos conservadores;
- stopwords gerais e termos jurídicos excessivamente genéricos.

Cada conceito contém ID, termos literais, expansões e peso máximo. Uma expansão
nunca pode valer mais que 40% do literal correspondente. Mudanças no léxico
incrementam `analyzer_version` e exigem benchmark.

## Planejamento de fontes

`AdaptiveSourcePlanner` recebe capabilities já registradas e não acessa rede.
Providers inelegíveis pelo router 0038 são excluídos antes do score.

Score de roteamento v1, de 0 a 100:

| Sinal | Pontos |
| --- | ---: |
| suporta pesquisa unificada e papel textual primário | 25 |
| suporta todos os filtros explícitos | 20 |
| grau/ramo/coleção compatíveis | 15 |
| gold/silver conforme catálogo gerado | 10/6 |
| texto integral/ementa comprovado | 10/6 |
| live válido e recente | 10 |
| latência histórica p75 abaixo de 4 s / 8 s | 6/3 |
| estabilidade sem drift recente | 4 |

Penalidades: contextual `-25` quando não solicitado; live desconhecido `-8`;
parcial `-15`; blocked/unavailable exclui. Dados ausentes não recebem bônus.

Seleção:

1. ordenar por score, source ID como desempate;
2. reservar no máximo 35% das vagas para a mesma autoridade/tribunal;
3. incluir ao menos três autoridades quando disponíveis;
4. preencher até 8 fontes; ampliar até 12 se houver candidatos com score >= 55;
5. onda rápida: três menores latências entre os seis maiores scores;
6. onda complementar: próximos quatro;
7. onda de cobertura: restantes;
8. `selected` preserva exatamente a escolha após validação;
9. `all` usa todas as fontes elegíveis em lotes existentes.

Sem histórico de latência, usar faixa neutra e desempate estável, nunca valor
aleatório.

## Plano por provider

`ProviderQueryPlan` contém:

```text
source, wave, remote_query, page, page_size, timeout_ms,
filters_native, filters_translated, filters_local,
filters_unsupported, contract_version, capability_fingerprint
```

- page size padrão por fonte: `min(20, capability.max_remote_page_size)`;
- orçamento por fonte é redistribuído sem ultrapassar 240;
- filtros explícitos unsupported geram warning; identificadores unsupported
  preservam a regra de skip do router atual;
- filtros inferidos ambíguos ficam apenas em `suggested_filters`;
- uma requisição por provider no fluxo padrão; paginação adicional somente no
  modo all ou página posterior explicitamente solicitada.

## Outcome de fonte

Adicionar `outcome_status` ao envelope consolidado sem quebrar
`source_outcomes` existente. Mapeamento obrigatório:

| Evidência | Status novo |
| --- | --- |
| resultados válidos | `success_with_results` |
| zero + `total_known=true` ou `is_complete=true` | `authoritative_empty` |
| zero sem prova | `unconfirmed_empty` |
| timeout/deadline | `timeout` |
| 401/403/login/CAPTCHA/WAF | `access_blocked` |
| 429 | `rate_limited` |
| TLS/proxy/rede/5xx esgotado | `transport_error` |
| parser/shape/MIME incompatível | `schema_invalid` |
| registros válidos + falhas/truncamento | `partial` |
| abort do usuário | `cancelled` |

## Ranker v1

### Componente lexical BM25 (`bm25-v1`)

O ranker v1 incorpora um sinal BM25 fieldado, calculado somente sobre o lote
limitado de candidatos retornado pela busca live. Ele usa `k1=1.2`, `b=0.75`,
IDF suavizado e os pesos de campo já definidos nesta seção. A pontuação é
normalizada para `[0,1]` antes de entrar na fórmula global, com peso de 0,10;
identificador CNJ exato continua com precedência absoluta.

Esse componente não cria índice, não persiste corpus e não consulta serviço
externo: frequências documentais e comprimento médio são descartados ao final
de cada chamada. A comparação BM25 é válida apenas dentro do lote materializado
pela chamada; a ordenação entre ondas continua sendo feita pelo ranker global
após a consolidação dos candidatos. A versão do componente (`bm25-v1`) é
exposta na anotação de cada resultado para auditoria e reprodução.

### Texto por campo

Nota de compatibilidade: a cobertura de termos com pesos estaticos continua
independente. O componente BM25 usa IDF suavizado apenas no lote consolidado e
nao produz um score comparavel entre ondas isoladas.

Extrair valores com limite antes de normalizar:

| Campo | Limite | Peso |
| --- | ---: | ---: |
| case_number/registry/number | 128 | 10.0 |
| thesis/question/subject/title | 2 KiB | 5.0 |
| summary/ementa | 8 KiB | 4.0 |
| case_class/document_type/decision_type | 512 | 3.0 |
| judging_body/rapporteur/legal_area | 1 KiB | 2.0 |
| full_text | 16 KiB | 1.0 |

Nunca serializar `raw` inteiro para o ranker. Campos raw só podem ser usados por
aliases allowlisted e limitados.

### Sinais e fórmula

Todos os componentes são normalizados em `[0, 1]`:

```text
lexical = 0.25 * weighted_term_coverage
        + 0.10 * bm25_batch_score
        + 0.22 * exact_phrase
        + 0.14 * proximity
        + 0.12 * legal_concept_coverage
        + 0.08 * field_quality
        + 0.06 * explicit_filter_consistency
        + 0.03 * native_rank_rrf

score = 100 * clamp(lexical - penalties, 0, 1)
```

- cobertura usa termos únicos e pesos estáticos versionados: termo jurídico
  específico 1,0, termo comum 0,6, termo genérico 0,3 e expansão até 0,4. Não
  usa IDF dependente do lote, pois isso tornaria ondas incomparáveis;
- frase exata vale 1 no assunto/tese/ementa, 0,7 no texto integral e 0 fora;
- proximidade usa menor janela ordenada, limitada a 50 tokens;
- conceitos literais valem 1; expansões até 0,4;
- rank nativo usa `1/(20 + rank)` normalizado para rank 1;
- identificador CNJ exato força score mínimo 99,9;
- desempate: score, cobertura literal, qualidade, source, id;
- datas não pontuam salvo filtro temporal explícito; nesse caso só validam
  consistência, não “novidade”.

Penalidades máximas:

| Condição | Penalidade |
| --- | ---: |
| menos de 50% dos termos essenciais | 0.30 |
| match apenas em termo genérico | 0.25 |
| conflito explícito de grau/tipo/ramo | rejeitar antes do ranking |
| fonte contextual fora da intenção | 0.20 |
| ausência de conteúdo textual primário | 0.18 |
| extração parcial/garbled | 0.10 |
| filtro relevante unsupported | 0.08 por filtro, máximo 0.20 |

O score público terá uma casa decimal. Features detalhadas ficam internas; a
API retorna somente razões allowlisted e valores necessários à auditoria.

### Razões

Gerar no máximo três, em ordem:

1. identificador exato;
2. expressão exata no campo de maior peso;
3. cobertura `N/N` dos conceitos/termos;
4. tipo/grau/classe explicitamente compatível;
5. inteiro teor disponível;
6. correspondência na ementa.

Uma razão só aparece se seu sinal for maior que zero.

## Deduplicação

Fases:

1. identidade canônica existente;
2. CNJ + tribunal + tipo + data;
3. documento URL/hash equivalente;
4. fingerprint de texto normalizado + tribunal + órgão + data.

Similaridade aproximada só agrupa quando todos os metadados fortes compatíveis
e a semelhança de shingles 5-gram for >= 0,92. Termos `retificação`,
`republicação`, versões ou datas divergentes impedem fusão automática. O melhor
item representa o grupo; `duplicate_sources` e `deduplication_group` preservam
a composição.

Diversidade aplica penalidade máxima de 5 pontos apenas a itens a menos de 3
pontos entre si e repetidos consecutivamente da mesma fonte. Não afeta match
exato nem conflitos maiores que 3 pontos.

## APIs

### Requisição

Campos aditivos:

```json
{
  "mode": "adaptive",
  "query": "acórdãos sobre divórcio",
  "sources": [],
  "types": [],
  "page": 1,
  "page_size": 10,
  "filters": {},
  "ranking_version": "legal-live-v1"
}
```

- ausência de `mode`: `selected` se `sources` não vazio; comportamento legado
  se vazio até a feature flag ser ativada;
- com flag ativa e `sources` vazio: `adaptive`;
- versão desconhecida retorna 422, nunca fallback silencioso.

### Resposta

Campos aditivos de topo:

```text
query_intent, search_plan, source_outcomes_v2, result_rankings,
ranking_version, ranking_complete, candidate_count
```

`result_rankings` é um mapa pela identidade canônica. Ranking é específico da
consulta e não será gravado dentro de `CanonicalDecision` ou
`CanonicalPrecedent`. Na projeção da plataforma, cada item recebe um objeto
aninhado `ranking`:

```text
relevance_score, matched_terms, matched_concepts, match_reasons,
native_rank, deduplication_group, duplicate_sources
```

Projeções browser/research devem copiar esses campos explicitamente. `raw`,
features internas, texto excedente e query remota sensível não cruzam a API.

## Execução progressiva web

Por compatibilidade com OCI Functions/API Gateway, não depender de SSE.

- adicionar `POST /api/v1/search/plan`, autenticado e sem chamadas a providers;
- `adaptive`: o browser obtém o plano e chama `/api/v1/search` sequencialmente
  para cada onda, sem atraso artificial, evitando bursts no SearchGuard;
- cada chamada inclui o mesmo `plan_id`, `ranking_version` e sources daquela
  onda;
- o backend recomputa o plano a partir da query/filtros e valida `plan_id`, onda
  e sources; o ID é SHA-256 dos inputs normalizados, capability fingerprint e
  versões. Ele não concede autorização e não precisa de estado nem secret;
- cada resposta já contém score absoluto comparável;
- `mergeBatchResults` deduplica, ordena por score/desempate e recalcula páginas;
- `all`: reutiliza os lotes de até 12, mas aplica o mesmo merge ranqueado.

## Freeze de interface

Estado novo:

```text
rankingFrozen, pendingRankedPayload, freezeReason, searchGeneration
```

Congelar em clique de resultado, abertura do leitor, seleção de texto não vazia,
foco por teclado em cartão e scroll acumulado >= 120 px após primeira onda.
Não congelar por foco automático inicial. Ao receber nova onda congelada,
manter DOM/seleção e exibir botão “Aplicar resultados mais relevantes”. Nova
consulta zera o freeze. Resposta de geração anterior é descartada.

## Cache

- somente cache atual do `SearchGuard` ou equivalente efêmero;
- chave inclui fingerprint da query/filters/sources, capability fingerprint,
  analyzer e ranking versions;
- TTL default 10 minutos, configurável entre 5 e 15;
- não permitir enumeração ou busca por conteúdo do cache;
- stale só retorna com `cache_status=stale` e outcome original preservado;
- corpos e textos não entram em telemetria.

## Telemetria

Feature separada e desligada por padrão local. Evento allowlisted:

```text
event_type, occurred_at, daily_session_id, query_hmac,
intent_categories, ranking_version, source, canonical_result_id,
rank, dwell_bucket, latency_bucket, source_outcome
```

HMAC usa secret e rotação diária. Não registrar query, e-mail, subject, IP,
ementa, inteiro teor ou raw. Retenção 30 dias por TTL. Falta de secret desliga
telemetria, não impede busca.

## Compatibilidade e migração

- registros canônicos permanecem independentes da consulta; o ranking fica no
  sidecar `result_rankings` e no objeto `ranking` da projeção web;
- consumidores legados podem ignorar campos novos;
- `search_many` mantém assinatura e paginação;
- feature flag mantém `_rank_and_deduplicate` anterior como rollback temporário;
- remover o ranker antigo só em mudança futura após rollout comprovado;
- não alterar providers individualmente nesta mudança, salvo correção mínima de
  metadata necessária e já comprovada.

## Operação

- métricas: analyzer/ranker duration, time-to-first-wave, consolidation time,
  candidates, outcomes e cache status;
- logs estruturados sem query em claro;
- readiness não depende de tribunal externo;
- rollback por `NANOJURIS_LIVE_RANKING_VERSION=legacy`;
- shadow calcula os dois rankings sobre os mesmos candidatos e expõe apenas o
  antigo; telemetria guarda apenas métricas agregadas de divergência.

## ADRs

- `adrs/ADR-0077-001-live-only.md`.
- `adrs/ADR-0077-002-deterministic-ranking.md`.
- `adrs/ADR-0077-003-progressive-waves.md`.
