# Surface workpack — `surface:trf5:jurisprudencia:second:trf5-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:trf5:jurisprudencia:second:trf5-jurisprudencia
authority: TRF5
branch: federal
degree: second
instance: second
collection: JURISPRUDENCIA
provider: trf5_jurisprudencia
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/trf5-live-20260908-cycle72.json`
- `docs/providers/trf5_jurisprudencia/README.md`
- `provider-catalog:trf5_jurisprudencia`

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
    "informativo",
    "sumula"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
