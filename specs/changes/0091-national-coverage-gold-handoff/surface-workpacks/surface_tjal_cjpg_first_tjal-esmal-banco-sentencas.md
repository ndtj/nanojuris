# Surface workpack — `surface:tjal:cjpg:first:tjal-esmal-banco-sentencas`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjal:cjpg:first:tjal-esmal-banco-sentencas
authority: TJAL
branch: state
degree: first
instance: first
collection: CJPG
provider: tjal_esmal_banco_sentencas
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/tjal-esmal-banco-sentencas-live-20260908.json`
- `docs/provider-discovery/tjal-esmal-banco-sentencas-live-20260909.json`
- `docs/providers/tjal_esmal_banco_sentencas/README.md`
- `provider-catalog:tjal_esmal_banco_sentencas`

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

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
