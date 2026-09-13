# Surface workpack — `surface:tjes:turma-recursal:recursal:tjes-turma-recursal`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjes:turma-recursal:recursal:tjes-turma-recursal
authority: TJES
branch: state
degree: recursal
instance: recursal
collection: TURMA_RECURSAL
provider: tjes_turma_recursal
required: false
lifecycle: implemented
contract_status: live_validated
live_status: valid
federation_status: enabled
legal_status: operator_approved
```

## Evidence

- `docs/provider-discovery/federated-promotion-live-20260906-legitimate-recheck.json`
- `docs/providers/tjes_turma_recursal/README.md`
- `provider-catalog:tjes_turma_recursal`

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
    "text"
  ],
  "document_types": [
    "acordao",
    "recurso_inominado"
  ]
}
```

## Next action

maintain TTL smoke and monitor schema drift

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
