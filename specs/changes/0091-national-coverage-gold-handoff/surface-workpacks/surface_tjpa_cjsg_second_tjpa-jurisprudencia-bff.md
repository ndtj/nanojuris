# Surface workpack — `surface:tjpa:cjsg:second:tjpa-jurisprudencia-bff`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjpa:cjsg:second:tjpa-jurisprudencia-bff
authority: TJPA
branch: state
degree: second
instance: second
collection: CJSG
provider: tjpa_jurisprudencia_bff
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/state-b1-live-20260908-cycle70.json`
- `docs/providers/tjpa_jurisprudencia_bff/README.md`
- `provider-catalog:tjpa_jurisprudencia_bff`

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
    "json"
  ],
  "document_types": [
    "acordao",
    "decisao_monocratica"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
