# Surface workpack — `surface:tjrj:cjpg:first:tjrj-eproc-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjrj:cjpg:first:tjrj-eproc-jurisprudencia
authority: TJRJ
branch: state
degree: first
instance: first
collection: CJPG
provider: tjrj_eproc_jurisprudencia
required: true
lifecycle: implemented
contract_status: pending_contract
live_status: valid
federation_status: not_enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/state-eproc-degree-live-20260906.json`
- `docs/provider-discovery/state-eproc-degree-live-20260908.json`
- `docs/providers/tjrj_eproc_jurisprudencia/README.md`
- `provider-catalog:tjrj_eproc_jurisprudencia`

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
  "full_text_access": "detail_call",
  "formats": [
    "html"
  ],
  "document_types": [
    "acordao",
    "decisao_monocratica",
    "sumula",
    "despacho",
    "sentenca"
  ]
}
```

## Next action

close the degree-specific contract with bounded public evidence

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
