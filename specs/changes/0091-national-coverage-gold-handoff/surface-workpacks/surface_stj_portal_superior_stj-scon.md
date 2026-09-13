# Surface workpack — `surface:stj:portal:superior:stj-scon`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:stj:portal:superior:stj-scon
authority: STJ
branch: superior
degree: superior
instance: superior
collection: PORTAL
provider: stj_scon
required: true
lifecycle: implemented
contract_status: blocked_access
live_status: access_control_required
federation_status: blocked
legal_status: pending_human_review
```

## Evidence

- `docs/provider-discovery/document-qa-cycle-20260907-batch09.json`
- `docs/providers/stj_scon/README.md`
- `provider-catalog:stj_scon`

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
  "full_text_access": "detail_call",
  "formats": [
    "html",
    "pdf"
  ],
  "document_types": [
    "acordao"
  ]
}
```

## Next action

record official access state once and evaluate an authorized alternative

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
