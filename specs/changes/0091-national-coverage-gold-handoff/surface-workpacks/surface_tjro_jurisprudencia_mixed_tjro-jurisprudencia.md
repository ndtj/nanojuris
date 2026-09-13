# Surface workpack — `surface:tjro:jurisprudencia:mixed:tjro-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjro:jurisprudencia:mixed:tjro-jurisprudencia
authority: TJRO
branch: state
degree: mixed
instance: mixed
collection: JURISPRUDENCIA
provider: tjro_jurisprudencia
required: false
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/gold-document-probe-live-20260909.json`
- `docs/provider-discovery/tjro-cjpg-live-20260906.json`
- `docs/provider-discovery/tjro-cjsg-live-20260906.json`
- `docs/providers/tjro_jurisprudencia/README.md`
- `provider-catalog:tjro_jurisprudencia`

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
    "html",
    "text",
    "pdf",
    "docx"
  ],
  "document_types": [
    "decision",
    "sentence",
    "vote",
    "acordao"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
