# Contrato de API — busca live v1

## Compatibilidade

Todos os campos são aditivos. Requisições antigas continuam válidas. Ranking é
específico da consulta e não altera os modelos canônicos persistíveis.

## POST `/api/v1/search/plan`

Requisição autenticada:

```json
{
  "query": "acórdãos sobre divórcio",
  "mode": "adaptive",
  "sources": [],
  "types": [],
  "filters": {},
  "page_size": 10,
  "ranking_version": "legal-live-v1"
}
```

Resposta:

```json
{
  "plan_id": "sha256:...",
  "mode": "adaptive",
  "query_intent": {
    "original_query": "acórdãos sobre divórcio",
    "normalized_query": "acordaos sobre divorcio",
    "normalized_terms": ["divorcio"],
    "phrases": ["divorcio"],
    "required_terms": [],
    "optional_terms": ["divorcio"],
    "excluded_terms": [],
    "legal_concepts": [{"id": "family.divorce", "weight": 1.0}],
    "detected_filters": {"document_type": "acordao"},
    "suggested_filters": {},
    "ambiguous_interpretations": [],
    "is_exact_identifier": false,
    "analyzer_version": "legal-query-v1"
  },
  "source_waves": [
    {"wave": 1, "sources": ["...", "...", "..."], "candidate_limit": 60},
    {"wave": 2, "sources": ["...", "...", "...", "..."], "candidate_limit": 80},
    {"wave": 3, "sources": ["..."], "candidate_limit": 100}
  ],
  "candidate_budget": 240,
  "ranking_version": "legal-live-v1"
}
```

O `plan_id` é hash determinístico dos inputs normalizados, fontes/ondas,
capability fingerprint e versões. Ele não é credencial. A resposta nunca inclui
score interno de provider nem query remota completa.

## POST `/api/v1/search`

Campos adicionais:

```json
{
  "mode": "adaptive",
  "plan_id": "sha256:...",
  "wave": 1,
  "ranking_version": "legal-live-v1"
}
```

Para `adaptive`, o backend recomputa o plano e rejeita com 409 plano obsoleto ou
com 422 sources/onda incompatíveis. Para `selected` e `all`, `plan_id` e `wave`
são opcionais.

Resposta aditiva:

```json
{
  "ranking_version": "legal-live-v1",
  "ranking_complete": false,
  "candidate_count": 42,
  "query_intent": {},
  "search_plan": {},
  "source_outcomes_v2": [
    {
      "provider": "tjdf_juris",
      "status": "success_with_results",
      "latency_ms": 932,
      "pages": 1,
      "candidate_count": 20,
      "total_state": "unknown",
      "filters_applied": {},
      "filters_local": {},
      "filters_unsupported": []
    }
  ],
  "result_rankings": {
    "canonical-identity": {
      "relevance_score": 91.4,
      "bm25_score": 0.94,
      "bm25_version": "bm25-v1",
      "matched_terms": ["divorcio"],
      "matched_concepts": ["family.divorce"],
      "match_reasons": ["Expressão exata na ementa", "Acórdão compatível"],
      "native_rank": 2,
      "deduplication_group": "...",
      "duplicate_sources": []
    }
  },
  "results": []
}
```

Na API web, cada resultado projetado recebe `ranking` com a entrada sidecar.
`bm25_score` e `bm25_version` identificam o sinal lexical fieldado calculado
no lote live; esse sinal nao representa um indice persistente.
O envelope tambem inclui `bm25_version` quando `legal-live-v1` esta ativo,
mesmo que a coleta nao produza candidatos.
correspondente. O sidecar completo pode ser omitido da resposta web após essa
junção para reduzir payload.

## Validação e limites

- `mode`: somente `adaptive`, `selected`, `all`.
- `ranking_version`: `legacy` ou versão registrada.
- `wave`: 1–3 e obrigatória apenas em plano adaptive progressivo.
- body, query, filtros e sources mantêm limites existentes.
- máximo 12 sources por chamada, 20 candidatos por provider e 240 no plano.
- strings de razões vêm de catálogo interno; nunca do provider.
- versão desconhecida: 422.
- plano recalculado diferente: 409, permitindo ao browser solicitar novo plano.
- fonte fora do plano: 422.

## Erros públicos

Erros de provider permanecem dentro de `source_outcomes_v2` quando a busca pode
ser parcial. 4xx do endpoint só representa requisição/plano/autenticação
inválidos. Mensagens não incluem endpoint sensível, exception raw ou payload.
