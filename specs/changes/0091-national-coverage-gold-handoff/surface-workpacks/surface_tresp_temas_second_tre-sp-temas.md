# Surface workpack — `surface:tresp:temas:second:tre-sp-temas`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tresp:temas:second:tre-sp-temas
authority: TRESP
branch: electoral
degree: second
instance: second
collection: TEMAS
provider: tre_sp_temas
required: false
lifecycle: implemented
contract_status: source_unavailable
live_status: source_unavailable
federation_status: blocked
legal_status: pending_human_review
```

## Evidence

- `docs/providers/tre_sp_temas/README.md`
- `docs/validation/runs/20260905T082427Z-federated-live-20260905-cycle39.json`
- `provider-catalog:tre_sp_temas`

## Gates

| Gate | State |
| --- | --- |
| `official_source` | `passed` |
| `degree_contract` | `pending` |
| `runtime` | `passed` |
| `fixtures` | `passed` |
| `pagination_filters` | `pending` |
| `bounded_live` | `blocked` |
| `canonical_quality` | `pending` |
| `federation` | `blocked` |

## Document capability

```json
{
  "status": "declared",
  "supports_full_text": true,
  "full_text_access": "document_link",
  "formats": [
    "html",
    "pdf"
  ],
  "document_types": [
    "tema_selecionado"
  ]
}
```

## Next action

close the degree-specific contract with bounded public evidence

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
