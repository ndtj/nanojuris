# Surface workpack — `surface:tjes:cjsg:second:tjes-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjes:cjsg:second:tjes-jurisprudencia
authority: TJES
branch: state
degree: second
instance: second
collection: CJSG
provider: tjes_jurisprudencia
required: true
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/cjsg-live-20260908-cycle67.json`
- `docs/provider-discovery/tjes-cjsg-live-20260901.json`
- `docs/providers/tjes_jurisprudencia/README.md`
- `provider-catalog:tjes_jurisprudencia`

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
    "text",
    "html"
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
