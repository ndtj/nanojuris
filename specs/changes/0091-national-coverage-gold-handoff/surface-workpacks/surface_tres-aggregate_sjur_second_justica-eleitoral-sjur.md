# Surface workpack — `surface:tres-aggregate:sjur:second:justica-eleitoral-sjur`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tres-aggregate:sjur:second:justica-eleitoral-sjur
authority: TRES_AGGREGATE
branch: electoral
degree: second
instance: second
collection: SJUR
provider: justica_eleitoral_sjur
required: true
lifecycle: implemented
contract_status: pending_contract
live_status: source_unavailable
federation_status: not_enabled
legal_status: pending_human_review
```

## Evidence

- `docs/provider-discovery/document-qa-cycle-20260907-batch10.json`
- `docs/provider-discovery/tre-sjur-gold-live-20260909.json`
- `docs/provider-discovery/tre-sjur-route-inventory-live-20260909.json`
- `docs/provider-discovery/tre-sp-sjur-pagination-live-20260909.json`
- `docs/providers/justica_eleitoral_sjur/README.md`
- `provider-catalog:justica_eleitoral_sjur`

## Gates

| Gate | State |
| --- | --- |
| `official_source` | `passed` |
| `degree_contract` | `pending` |
| `runtime` | `passed` |
| `fixtures` | `passed` |
| `pagination_filters` | `pending` |
| `bounded_live` | `blocked` |
| `canonical_quality` | `pending` |
| `federation` | `pending` |

## Document capability

```json
{
  "status": "declared",
  "supports_full_text": false,
  "full_text_access": "not_available",
  "formats": [
    "json"
  ],
  "document_types": [
    "catalog_metadata"
  ]
}
```

## Next action

close the degree-specific contract with bounded public evidence

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
