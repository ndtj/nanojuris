# Surface workpack — `surface:tjmmg:portal:second:tjmmg-jurisprudencia-api`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjmmg:portal:second:tjmmg-jurisprudencia-api
authority: TJMMG
branch: military
degree: second
instance: second
collection: PORTAL
provider: tjmmg_jurisprudencia_api
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: not_enabled
legal_status: pending_human_review
```

## Evidence

- `docs/provider-discovery/tjm-mg-jurisprudencia-api-live-20260911.json`
- `docs/providers/tjmmg_jurisprudencia_api/README.md`
- `provider-catalog:tjmmg_jurisprudencia_api`

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
| `federation` | `pending` |

## Document capability

```json
{
  "status": "declared",
  "supports_full_text": true,
  "full_text_access": "inline",
  "formats": [
    "json",
    "pdf"
  ],
  "document_types": [
    "acordao",
    "decisao"
  ]
}
```

## Next action

run opt-in federation smoke and preserve legal status separately

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
