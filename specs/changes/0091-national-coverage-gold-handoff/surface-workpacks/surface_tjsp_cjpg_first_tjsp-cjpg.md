# Surface workpack — `surface:tjsp:cjpg:first:tjsp-cjpg`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjsp:cjpg:first:tjsp-cjpg
authority: TJSP
branch: state
degree: first
instance: first
collection: CJPG
provider: tjsp_cjpg
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/degree-bindings-live-20260902-cycle26.json`
- `docs/providers/tjsp_cjpg/README.md`
- `provider-catalog:tjsp_cjpg`

## Gates

| Gate | State |
| --- | --- |
| `official_source` | `passed` |
| `degree_contract` | `passed` |
| `runtime` | `passed` |
| `fixtures` | `passed` |
| `pagination_filters` | `passed` |
| `bounded_live` | `passed` |
| `canonical_quality` | `passed` |
| `federation` | `passed` |

## Document capability

```json
{
  "status": "declared",
  "supports_full_text": true,
  "full_text_access": "inline",
  "formats": [
    "html",
    "text"
  ],
  "document_types": [
    "decisao_1g",
    "sentenca"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
