# Surface workpack — `surface:stf:portal:superior:stf-juris`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:stf:portal:superior:stf-juris
authority: STF
branch: constitutional
degree: superior
instance: superior
collection: PORTAL
provider: stf_juris
required: true
lifecycle: implemented
contract_status: blocked_transport
live_status: blocked_transport
federation_status: blocked
legal_status: pending_human_review
```

## Evidence

- `docs/provider-discovery/stf-juris-live-recheck-20260901-cycle9.json`
- `docs/providers/stf_juris/README.md`
- `provider-catalog:stf_juris`

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
  "supports_full_text": false,
  "full_text_access": "link_only",
  "formats": [
    "json"
  ],
  "document_types": [
    "acordao"
  ]
}
```

## Next action

record official access state once and evaluate an authorized alternative

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
