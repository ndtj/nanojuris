# Surface workpack — `surface:tjmt:jurisprudencia:second:tjmt-jurisprudencia-api`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjmt:jurisprudencia:second:tjmt-jurisprudencia-api
authority: TJMT
branch: state
degree: second
instance: second
collection: JURISPRUDENCIA
provider: tjmt_jurisprudencia_api
required: false
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/state-b1-live-20260908-cycle70.json`
- `docs/providers/tjmt_jurisprudencia_api/README.md`
- `provider-catalog:tjmt_jurisprudencia_api`

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
    "html",
    "text"
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
