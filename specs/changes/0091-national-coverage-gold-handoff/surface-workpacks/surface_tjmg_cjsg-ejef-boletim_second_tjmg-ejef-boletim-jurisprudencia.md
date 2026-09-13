# Surface workpack — `surface:tjmg:cjsg-ejef-boletim:second:tjmg-ejef-boletim-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjmg:cjsg-ejef-boletim:second:tjmg-ejef-boletim-jurisprudencia
authority: TJMG
branch: state
degree: second
instance: second
collection: CJSG_EJEF_BOLETIM
provider: tjmg_ejef_boletim_jurisprudencia
required: false
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/gold-document-probe-live-20260909.json`
- `docs/provider-discovery/tjmg-ejef-boletim-live-20260908.json`
- `docs/providers/tjmg_ejef_boletim_jurisprudencia/README.md`
- `provider-catalog:tjmg_ejef_boletim_jurisprudencia`

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
  "full_text_access": "document_link",
  "formats": [
    "json",
    "pdf",
    "text"
  ],
  "document_types": [
    "acordao",
    "ementa",
    "boletim"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
