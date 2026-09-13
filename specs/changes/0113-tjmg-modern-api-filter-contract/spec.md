# SDD 0113 - TJMG modern API filter contract alignment

Status: `verified`
Owner: Provider Engineering
Date: `2026-09-12`

## Objective

Align the TJMG CJSG adapter capabilities with the public modern API contract
already implemented in `_build_modern_payload`, so federated routing never
rejects a supported filter or silently ignores an explicit refinement.

## Scope

- Declare native filters for `types`, `document_type`, `decision_type`,
  `courts`, and `legal_area`.
- Preserve `exact_phrase` and `all_words` as translated free-text refinements.
- Reject `any_words` and `without_words`, whose independent semantics are not
  proven by the public API.
- Compile decision/document type aliases into the official `tiposDocumento`
  field without duplicates.
- Keep the legacy CAPTCHA form diagnostic-only and preserve CJSG/second-degree
  scope validation.

## Acceptance criteria

- AC-001: capabilities report the API-backed filters with correct semantics.
- AC-002: explicit unsupported filters fail before transport.
- AC-003: all accepted structured filters appear in the request payload.
- AC-004: existing pagination, full-text detail, access/error states and scope
  invariants remain unchanged.
- AC-005: fixtures and focused tests cover the new contract.

## Out of scope

- automating or bypassing the legacy CAPTCHA;
- asserting first-degree coverage for TJMG;
- changing production, release or deployment state.
