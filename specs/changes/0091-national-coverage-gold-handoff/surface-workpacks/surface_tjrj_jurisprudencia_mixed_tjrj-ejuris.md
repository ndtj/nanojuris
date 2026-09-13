# Surface workpack — `surface:tjrj:jurisprudencia:mixed:tjrj-ejuris`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjrj:jurisprudencia:mixed:tjrj-ejuris
authority: TJRJ
branch: state
degree: mixed
instance: mixed
collection: JURISPRUDENCIA
provider: tjrj_ejuris
required: false
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/tjrj-ejuris-pagination-live-20260910.json`
- `docs/providers/tjrj_ejuris/README.md`
- `provider-catalog:tjrj_ejuris`

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
    "html",
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
