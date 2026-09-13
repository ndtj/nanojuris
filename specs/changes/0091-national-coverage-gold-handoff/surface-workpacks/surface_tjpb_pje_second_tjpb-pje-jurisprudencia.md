# Surface workpack — `surface:tjpb:pje:second:tjpb-pje-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjpb:pje:second:tjpb-pje-jurisprudencia
authority: TJPB
branch: state
degree: second
instance: second
collection: PJE
provider: tjpb_pje_jurisprudencia
required: false
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/state-b1-live-20260908-cycle70.json`
- `docs/providers/tjpb_pje_jurisprudencia/README.md`
- `provider-catalog:tjpb_pje_jurisprudencia`

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
    "html"
  ],
  "document_types": [
    "jurisprudencia_pje",
    "acordao",
    "decisao"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
