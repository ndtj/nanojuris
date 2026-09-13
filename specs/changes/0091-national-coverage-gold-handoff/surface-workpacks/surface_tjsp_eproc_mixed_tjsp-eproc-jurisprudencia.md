# Surface workpack — `surface:tjsp:eproc:mixed:tjsp-eproc-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjsp:eproc:mixed:tjsp-eproc-jurisprudencia
authority: TJSP
branch: state
degree: mixed
instance: mixed
collection: EPROC
provider: tjsp_eproc_jurisprudencia
required: false
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/tjsp-eproc-live-20260905-cycle63.json`
- `docs/providers/tjsp_eproc_jurisprudencia/README.md`
- `provider-catalog:tjsp_eproc_jurisprudencia`

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
    "html"
  ],
  "document_types": [
    "sentenca",
    "acordao",
    "decisao_monocratica"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
