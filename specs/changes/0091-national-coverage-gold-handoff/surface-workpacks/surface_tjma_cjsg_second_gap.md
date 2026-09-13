# Surface workpack — `surface:tjma:cjsg:second:gap`

Generated from the canonical surface registry. This file records state; it does not promote a provider.

## Identity

```yaml
surface_id: surface:tjma:cjsg:second:gap
authority: TJMA
branch: state
degree: second
instance: second
collection: CJSG
provider: tjma_jurisconsult
required: true
lifecycle: candidate
contract_status: candidate
live_status: access_controlled
federation_status: not_enabled
legal_status: pending_human_review
```

## Evidence

- `docs/provider-discovery/state-cjsg-blocked-recheck-live-20260913.json`
- `docs/provider-discovery/tjma-jurisprudence-route-live-20260908.json`
- `docs/provider-discovery/tjma-jurisprudencia-captcha-live-20260906.json`
- `docs/provider-discovery/tjma-official-alternatives-live-20260907.json`
- `provider-catalog:tjma_jurisconsult`

## Gates

| Gate | State |
| --- | --- |
| `official_source` | `passed` |
| `degree_contract` | `pending` |
| `runtime` | `pending` |
| `fixtures` | `passed` |
| `pagination_filters` | `pending` |
| `bounded_live` | `blocked` |
| `canonical_quality` | `pending` |
| `federation` | `pending` |

## Document capability

```json
{
  "status": "unknown",
  "supports_full_text": false,
  "full_text_access": "unknown",
  "formats": [],
  "document_types": []
}
```

## Next action

record official access state once and evaluate an authorized alternative

External blocks, authentication, CAPTCHA, WAF, TLS, rate limits and schema drift are never treated as empty results.
