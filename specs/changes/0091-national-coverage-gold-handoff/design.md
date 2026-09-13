# Design — programa de cobertura nacional ouro

## 1. Fonte única e chave de superfície

O registro de execução é uma projeção gerada, nunca editada à mão. A chave
imutável é:

```text
surface_id = authority/branch/degree/instance/collection/document_scope
```

Cada item possui, no mínimo:

```text
authority, branch, degree, instance, collection, provider,
lifecycle, maturity, contract_status, live_status, quality_status,
document_capability, federation_status, legal_status,
last_live_check, evidence_ids, evidence_ttl, owner, next_action
```

As dimensões são ortogonais. `runtime=true` não implica `live_validated`; um
provider pode ser tecnicamente ouro e continuar fora da federação por bloqueio
externo ou decisão humana.

## 2. Pipeline por fonte

```text
catalog -> official discovery -> contract ledger -> adapter
        -> source fixtures -> canonical validation -> document pipeline
        -> bounded live smoke -> opt-in federation -> technical promotion
        -> human/legal review -> default rollout
```

O transporte compartilhado controla timeout, limites, retries transitórios,
backoff, cache efêmero, circuit breaker, redaction e correlação. O adapter
conhece apenas a semântica do tribunal: rota, método, payload, seletores,
enumerações, grau, filtros, paginação e erros.

## 3. Contratos de capacidade

Cada filtro e campo é representado por uma linha do ledger:

```json
{
  "capability_id": "tjxx/search/case_class",
  "kind": "filter",
  "canonical_name": "case_class",
  "native_name": "classe",
  "support_state": "native",
  "values": [],
  "evidence_ids": [],
  "last_verified_at": null,
  "ttl_days": 30
}
```

O envelope federado informa quatro conjuntos: `remote_applied`,
`translated`, `local_postfilter` e `unsupported`. Filtro explícito sem prova
não desaparece silenciosamente.

## 4. Estados de execução

```text
success_with_results | authoritative_empty | unconfirmed_empty |
partial | access_blocked | challenge_incidental | challenge_enforced |
rate_limited | timeout | transport_error | tls_error | schema_invalid |
source_unavailable | cancelled
```

`challenge_incidental` só existe quando a página pública prossegue sem solver,
sem token persistido e sem interação automatizada com o desafio. Se a fonte
exigir ação humana, a execução termina em `challenge_enforced`.

## 5. Documentos

```text
decision -> allowlisted detail URL -> bounded fetch -> redirect validation
         -> MIME/magic/size/hash -> HTML/PDF/text extraction
         -> CanonicalDocument + provenance
```

OCR é opcional, isolado, limitado e permitido apenas para o documento público;
nunca se aplica a CAPTCHA. PDF vazio, MIME incorreto, excesso de páginas ou
conteúdo malformado gera estado de extração explícito.

## 6. Busca web sem índice

O SDD 0077 fornece análise determinística da consulta, planner de 8–12 fontes,
ondas, ranker CPU-only, deduplicação e congelamento após interação. Este pacote
exige que os resultados incluam status por fonte, filtros e completude. Cache
efêmero de resposta é permitido; não há corpus pesquisável persistido.

## 7. Equivalência Juscraper

Para cada módulo correspondente:

1. registrar a licença e o commit observado;
2. comparar rota, payload, seletores e paginação;
3. confirmar que a rota oficial ainda está pública;
4. implementar parser NanoJuris independente;
5. gerar fixture sanitizada e teste diferencial;
6. registrar diferenças, limites e decisão de promoção.

Juscraper é evidência de descoberta, não prova de disponibilidade atual nem
autorização para copiar código ou contornar controles.

## 8. Idempotência e qualidade

Chaves canônicas combinam autoridade, identificador, número, data, órgão e
fingerprint. Republicações e retificações comprovadas permanecem distintas.
O ranking final é determinístico e independente da ordem das respostas. Toda
saída carrega `parser_version`, `schema_version`, `ranking_version`,
`source_trace` e `completeness`.
