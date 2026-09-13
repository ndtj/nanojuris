# Surface workpack — `surface:tjpe:jurisprudencia:second:tjpe-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjpe:jurisprudencia:second:tjpe-jurisprudencia
authority: TJPE
branch: state
degree: second
instance: second
collection: JURISPRUDENCIA
provider: tjpe_jurisprudencia
required: false
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/cjsg-live-20260908-cycle67.json`
- `docs/providers/tjpe_jurisprudencia/README.md`
- `provider-catalog:tjpe_jurisprudencia`

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
    "html"
  ],
  "document_types": [
    "acordao",
    "decisao"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
