# Surface workpack — `surface:tjrn:jurisprudencia:mixed:tjrn-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjrn:jurisprudencia:mixed:tjrn-jurisprudencia
authority: TJRN
branch: state
degree: mixed
instance: mixed
collection: JURISPRUDENCIA
provider: tjrn_jurisprudencia
required: false
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/gold-document-probe-live-20260909.json`
- `docs/provider-discovery/tjrn-cjsg-live-20260906.json`
- `docs/providers/tjrn_jurisprudencia/README.md`
- `provider-catalog:tjrn_jurisprudencia`

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
    "text"
  ],
  "document_types": [
    "acordao",
    "decisao_monocratica",
    "sentenca"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
