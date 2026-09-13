# Surface workpack — `surface:tjmg:cjsg:second:tjmg-dspace-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjmg:cjsg:second:tjmg-dspace-jurisprudencia
authority: TJMG
branch: state
degree: second
instance: second
collection: CJSG
provider: tjmg_dspace_jurisprudencia
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/federated-promotion-live-20260906-legitimate-recheck.json`
- `docs/provider-discovery/tjmg-dspace-jurisprudencia-live-20260906.json`
- `docs/providers/tjmg_dspace_jurisprudencia/README.md`
- `provider-catalog:tjmg_dspace_jurisprudencia`

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
    "json",
    "pdf",
    "text"
  ],
  "document_types": [
    "acordao",
    "ementa"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
