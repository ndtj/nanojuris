# Surface workpack — `surface:tjma:catalog:unknown:tjma-jurisconsult`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjma:catalog:unknown:tjma-jurisconsult
authority: TJMA
branch: state
degree: unknown
instance: unknown
collection: CATALOG
provider: tjma_jurisconsult
required: false
lifecycle: implemented
contract_status: blocked_access
live_status: access_controlled
federation_status: blocked
legal_status: pending_human_review
```

## Evidence

- `docs/provider-discovery/state-cjsg-blocked-recheck-live-20260913.json`
- `docs/providers/tjma_jurisconsult/README.md`
- `provider-catalog:tjma_jurisconsult`

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
  "supports_full_text": false,
  "full_text_access": "access_blocked",
  "formats": [
    "json"
  ],
  "document_types": [
    "acordao",
    "decisao_monocratica",
    "sentenca",
    "sumula"
  ]
}
```

## Next action

record official access state once and evaluate an authorized alternative

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
