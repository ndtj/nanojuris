# Surface workpack — `surface:trepr:sjur:second:tre-sjur-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:trepr:sjur:second:tre-sjur-jurisprudencia
authority: TREPR
branch: electoral
degree: second
instance: second
collection: SJUR
provider: tre_sjur_jurisprudencia
required: true
lifecycle: implemented
contract_status: pending_contract
live_status: partial
federation_status: not_enabled
legal_status: pending_human_review
```

## Evidence

- `docs/provider-discovery/tre-sjur-date-partition-uf-sweep-live-20260913.json`
- `docs/provider-discovery/tre-sjur-document-uf-sweep-live-20260913.json`
- `docs/provider-discovery/tre-sjur-gold-live-20260909.json`
- `docs/provider-discovery/tre-sjur-pagination-recheck-live-20260913.json`
- `docs/provider-discovery/tre-sjur-route-inventory-live-20260909.json`
- `docs/provider-discovery/tre-sp-sjur-pagination-live-20260909.json`
- `docs/provider-discovery/tre-sp-sjur-runtime-live-20260910.json`
- `docs/providers/tre_sjur_jurisprudencia/README.md`
- `provider-catalog:tre_sjur_jurisprudencia`

## Gates

| Gate | State |
| --- | --- |
| `official_source` | `passed` |
| `degree_contract` | `pending` |
| `runtime` | `passed` |
| `fixtures` | `passed` |
| `pagination_filters` | `pending` |
| `bounded_live` | `pending` |
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
    "decisao",
    "resolucao"
  ]
}
```

## Next action

close the degree-specific contract with bounded public evidence

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
