# Surface workpack — `surface:tjrr:cjsg:second:tjrr-juris`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjrr:cjsg:second:tjrr-juris
authority: TJRR
branch: state
degree: second
instance: second
collection: CJSG
provider: tjrr_juris
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/tjrr-live-20260905-cycle57.json`
- `docs/provider-discovery/tjrr-live-20260913.json`
- `docs/providers/tjrr_juris/README.md`
- `provider-catalog:tjrr_juris`

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
    "html",
    "text"
  ],
  "document_types": [
    "acordao",
    "monocratic_decision"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
