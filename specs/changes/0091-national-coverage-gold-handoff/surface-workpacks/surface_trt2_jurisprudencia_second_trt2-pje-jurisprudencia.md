# Surface workpack — `surface:trt2:jurisprudencia:second:trt2-pje-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:trt2:jurisprudencia:second:trt2-pje-jurisprudencia
authority: TRT2
branch: labor
degree: second
instance: second
collection: JURISPRUDENCIA
provider: trt2_pje_jurisprudencia
required: true
lifecycle: candidate
contract_status: candidate
live_status: access_control_required
federation_status: not_enabled
legal_status: pending_human_review
```

## Evidence

- `docs/provider-discovery/trt2-pje-jurisprudencia-live-20260910.json`
- `docs/providers/trt2_pje_jurisprudencia/README.md`
- `provider-catalog:trt2_pje_jurisprudencia`

## Gates

| Gate | State |
| --- | --- |
| `official_source` | `passed` |
| `degree_contract` | `pending` |
| `runtime` | `pending` |
| `fixtures` | `pending` |
| `pagination_filters` | `pending` |
| `bounded_live` | `blocked` |
| `canonical_quality` | `pending` |
| `federation` | `pending` |

## Document capability

```json
{
  "status": "declared",
  "supports_full_text": false,
  "full_text_access": "access_blocked",
  "formats": [
    "json",
    "html"
  ],
  "document_types": [
    "acordao",
    "decisao"
  ]
}
```

## Next action

record official access state once and evaluate an authorized alternative

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
