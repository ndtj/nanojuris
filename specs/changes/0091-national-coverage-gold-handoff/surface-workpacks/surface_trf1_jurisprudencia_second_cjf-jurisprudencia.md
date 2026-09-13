# Surface workpack — `surface:trf1:jurisprudencia:second:cjf-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:trf1:jurisprudencia:second:cjf-jurisprudencia
authority: TRF1
branch: federal
degree: second
instance: second
collection: JURISPRUDENCIA
provider: cjf_jurisprudencia
required: true
lifecycle: implemented
contract_status: blocked_access
live_status: access_control_required
federation_status: blocked
legal_status: pending_human_review
```

## Evidence

- `docs/provider-discovery/document-qa-cycle-20260907-batch10.json`
- `docs/providers/cjf_jurisprudencia/README.md`
- `provider-catalog:cjf_jurisprudencia`

## Gates

| Gate | State |
| --- | --- |
| `official_source` | `passed` |
| `degree_contract` | `pending` |
| `runtime` | `passed` |
| `fixtures` | `passed` |
| `pagination_filters` | `pending` |
| `bounded_live` | `blocked` |
| `canonical_quality` | `pending` |
| `federation` | `blocked` |

## Document capability

```json
{
  "status": "declared",
  "supports_full_text": true,
  "full_text_access": "detail_call",
  "formats": [
    "html"
  ],
  "document_types": [
    "acordao",
    "sumula",
    "arguicao",
    "decisao_monocratica"
  ]
}
```

## Next action

record official access state once and evaluate an authorized alternative

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
