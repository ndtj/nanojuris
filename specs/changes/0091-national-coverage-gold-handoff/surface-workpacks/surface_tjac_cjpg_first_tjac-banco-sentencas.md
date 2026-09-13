# Surface workpack — `surface:tjac:cjpg:first:tjac-banco-sentencas`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjac:cjpg:first:tjac-banco-sentencas
authority: TJAC
branch: state
degree: first
instance: first
collection: CJPG
provider: tjac_banco_sentencas
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: not_enabled
legal_status: pending_human_review
```

## Evidence

- `docs/provider-discovery/tjac-banco-sentencas-live-20260912.json`
- `docs/providers/tjac_banco_sentencas/README.md`
- `provider-catalog:tjac_banco_sentencas`

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
  "full_text_access": "document_link",
  "formats": [
    "html",
    "pdf",
    "text"
  ],
  "document_types": [
    "sentenca"
  ]
}
```

## Next action

run opt-in federation smoke and preserve legal status separately

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
