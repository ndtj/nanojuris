# Surface workpack — `surface:stj:aggregate:superior:stj-dados-abertos-jurisprudencia`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:stj:aggregate:superior:stj-dados-abertos-jurisprudencia
authority: STJ
branch: superior
degree: superior
instance: superior
collection: AGGREGATE
provider: stj_dados_abertos_jurisprudencia
required: false
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: not_enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/stj-open-data-catalog-live-20260906.json`
- `docs/providers/stj_dados_abertos_jurisprudencia/README.md`
- `provider-catalog:stj_dados_abertos_jurisprudencia`

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
| `federation` | `pending` |

## Document capability

```json
{
  "status": "declared",
  "supports_full_text": true,
  "full_text_access": "detail_call",
  "formats": [
    "json",
    "csv",
    "zip"
  ],
  "document_types": [
    "acordao_espelho",
    "integra_decisao",
    "acordao_dje"
  ]
}
```

## Next action

run opt-in federation smoke and preserve legal status separately

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
