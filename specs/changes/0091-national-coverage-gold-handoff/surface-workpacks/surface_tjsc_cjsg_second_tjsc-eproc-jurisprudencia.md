# Surface workpack — `surface:tjsc:cjsg:second:tjsc-eproc-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjsc:cjsg:second:tjsc-eproc-jurisprudencia
authority: TJSC
branch: state
degree: second
instance: second
collection: CJSG
provider: tjsc_eproc_jurisprudencia
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/state-eproc-degree-live-20260906.json`
- `docs/provider-discovery/state-eproc-degree-live-20260908.json`
- `docs/providers/tjsc_eproc_jurisprudencia/README.md`
- `provider-catalog:tjsc_eproc_jurisprudencia`

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
    "acordao",
    "decisao_monocratica",
    "sumula",
    "despacho",
    "sentenca"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
