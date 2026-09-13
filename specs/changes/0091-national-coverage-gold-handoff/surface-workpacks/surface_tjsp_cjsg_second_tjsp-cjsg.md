# Surface workpack — `surface:tjsp:cjsg:second:tjsp-cjsg`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjsp:cjsg:second:tjsp-cjsg
authority: TJSP
branch: state
degree: second
instance: second
collection: CJSG
provider: tjsp_cjsg
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/tjsp-cjsg-live-20260913.json`
- `docs/providers/tjsp_cjsg/README.md`
- `provider-catalog:tjsp_cjsg`

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
  "full_text_access": "detail_call",
  "formats": [
    "html"
  ],
  "document_types": [
    "acordao",
    "monocratic_decision",
    "homologation"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
