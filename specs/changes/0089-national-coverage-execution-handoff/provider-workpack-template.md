# Template de workpack por provider

Copiar este modelo para `docs/providers/<source_id>/` e para o SDD específico
quando houver mudança de contrato.

## Identidade

```yaml
source_id: ""
authority: ""
branch: ""
degree: ""
instance: ""
collection: ""
coverage_role: "primary_textual_jurisprudence|curated|contextual"
```

## Fonte e acesso

```yaml
official_entrypoint: ""
routes:
  - method: GET
    url_template: ""
    payload: ""
    pagination: ""
    ordering: ""
access_class: "public|challenge_incidental|challenge_enforced|blocked|unavailable"
last_live_check: ""
evidence_ids: []
```

## Capabilities

Para cada filtro e campo, preencher `native`, `translated`, `local`,
`unsupported`, `blocked` ou `unknown`, com evidence id.

```yaml
filters: {}
fields: {}
document_capability: "inline|detail|download|ocr|not_offered|blocked|unknown"
total_state: "known|unknown|authoritative_zero"
```

## Fixtures e testes mínimos

- sucesso com registro textual;
- vazio autoritativo;
- parâmetro inválido;
- bloqueio/403/429/challenge;
- schema drift;
- segunda página ou cursor, se existir;
- filtros remotos e pós-filtros;
- autoridade/grau/coleção/identidade/datas;
- documento, MIME, hash, limite e trace.

## Decisão

```yaml
runtime: false
contract_status: pending
live_status: unknown
quality_status: pending
federation_status: opt_in
promotion_decision: pending
next_action: ""
```
