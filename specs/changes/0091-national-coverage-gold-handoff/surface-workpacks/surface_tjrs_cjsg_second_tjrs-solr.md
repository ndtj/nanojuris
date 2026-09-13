# Surface workpack — `surface:tjrs:cjsg:second:tjrs-solr`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjrs:cjsg:second:tjrs-solr
authority: TJRS
branch: state
degree: second
instance: second
collection: CJSG
provider: tjrs_solr
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/state-cjsg-live-20260908-cycle68.json`
- `docs/providers/tjrs_solr/README.md`
- `provider-catalog:tjrs_solr`

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
  "full_text_access": "detail_call",
  "formats": [
    "json",
    "tiff"
  ],
  "document_types": [
    "acordao",
    "decisao",
    "informativo",
    "inteiro_teor_tiff"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
