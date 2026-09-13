# Surface workpack — `surface:tjce:sjur:second:tjce-sjuris`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjce:sjur:second:tjce-sjuris
authority: TJCE
branch: state
degree: second
instance: second
collection: SJUR
provider: tjce_sjuris
required: false
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/tjce-sjuris-live-20260910-continue.json`
- `docs/providers/tjce_sjuris/README.md`
- `provider-catalog:tjce_sjuris`

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
    "json",
    "text",
    "pdf"
  ],
  "document_types": [
    "acordao",
    "decisao_monocratica",
    "sumula"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
