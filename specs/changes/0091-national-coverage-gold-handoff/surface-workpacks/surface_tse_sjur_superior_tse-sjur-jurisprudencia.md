# Surface workpack — `surface:tse:sjur:superior:tse-sjur-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tse:sjur:superior:tse-sjur-jurisprudencia
authority: TSE
branch: electoral
degree: superior
instance: superior
collection: SJUR
provider: tse_sjur_jurisprudencia
required: true
lifecycle: implemented
contract_status: pending_contract
live_status: valid
federation_status: not_enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/tse-sjur-scope-contract-live-20260912.json`
- `docs/provider-discovery/tse-sjur-search-live-20260909.json`
- `docs/providers/tse_sjur_jurisprudencia/README.md`
- `provider-catalog:tse_sjur_jurisprudencia`

## Gates

| Gate | State |
| --- | --- |
| `official_source` | `passed` |
| `degree_contract` | `pending` |
| `runtime` | `passed` |
| `fixtures` | `passed` |
| `pagination_filters` | `pending` |
| `bounded_live` | `passed` |
| `canonical_quality` | `pending` |
| `federation` | `pending` |

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

close the degree-specific contract with bounded public evidence

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
