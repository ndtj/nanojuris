# Design — programa nacional de providers

## Registro canônico de superfície

Chave estável:

```text
surface_id = authority/branch/degree/instance/collection/document_scope
```

Campos obrigatórios:

```text
authority, branch, degree, instance, collection, provider,
lifecycle, maturity, live_status, contract_status, document_capability,
quality_status, federation_status, legal_status, last_live_check,
evidence_ids, evidence_ttl, owner, next_action
```

Nenhuma dimensão substitui outra. `implemented` não significa `live_validated`
e `live_validated` não significa `federation_enabled`.

## Pipeline por provider

```text
official source -> bounded discovery -> contract -> adapter
-> fixtures -> canonical validation -> document validation
-> live smoke -> opt-in federation -> promotion manifest
```

O transporte compartilhado fornece timeout, tamanho máximo, retry transitório,
backoff, rate limit, cache efêmero, circuit breaker e redaction. O adapter
fornece apenas a semântica do tribunal: URL, payload, seletores, enumerações,
grau, paginação, filtros e erros.

## Estados de acesso

```text
success_with_results
authoritative_empty
unconfirmed_empty
partial
access_blocked
challenge_incidental
challenge_enforced
rate_limited
timeout
transport_error
tls_error
schema_invalid
source_unavailable
cancelled
```

`challenge_incidental` somente é permitido quando o fluxo público prossegue sem
token ou interação humana e devolve dados sem automação de desafio. Caso exija
solução, o estado é `challenge_enforced`.

## Matriz de filtros

Para cada campo do `SearchRequest`, persistir:

```text
requested_value, provider_value, support_state,
translation, local_predicate, evidence_id
```

A federação devolve os três conjuntos: aplicados remotamente, aplicados
localmente e não suportados. Um filtro explicitamente solicitado que não possa
ser provado não deve ser aplicado silenciosamente.

## Documentos

```text
result -> allowlisted detail URL -> bounded fetch
-> redirect validation -> MIME/magic/size -> SHA-256
-> HTML/PDF/text extraction -> CanonicalDocument + provenance
```

OCR é último recurso, somente para documento público permitido e em processo
isolado com limite de páginas/bytes. CAPTCHA nunca é OCRizado.

## Busca web

O SDD 0077 permanece responsável por intenção, planner, ondas, ranking e UX.
Este pacote somente exige que a federação consuma estados e traces corretos.
Sem índice próprio, a busca é limitada à janela live que cada autoridade
oferece; essa limitação deve aparecer na resposta.

## Idempotência e determinismo

- chaves canônicas combinam autoridade, número, data, órgão e fingerprint;
- versões/retificações preservadas como documentos distintos quando provadas;
- a ordem final independe da ordem de chegada das ondas;
- `parser_version`, `schema_version` e `ranking_version` acompanham a saída;
- reexecução bounded não duplica decisões.
