# Surface workpack — `surface:tjgo:cjsg:second:tjgo-projudi-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjgo:cjsg:second:tjgo-projudi-jurisprudencia
authority: TJGO
branch: state
degree: second
instance: second
collection: CJSG
provider: tjgo_projudi_jurisprudencia
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/tjgo-cjpg-live-20260906.json`
- `docs/provider-discovery/tjgo-cjsg-live-20260906-cycle58.json`
- `docs/provider-discovery/tjgo-projudi-live-20260910-continue.json`
- `docs/providers/tjgo_projudi_jurisprudencia/README.md`
- `provider-catalog:tjgo_projudi_jurisprudencia`

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
  "full_text_access": "inline_result_text",
  "formats": [
    "html"
  ],
  "document_types": [
    "decisao",
    "sentenca",
    "acordao"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
