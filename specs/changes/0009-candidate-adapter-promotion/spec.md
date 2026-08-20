# Spec — promoção segura de candidate adapters

ID: `0009-candidate-adapter-promotion`
Status: `in_progress`
Owner: `NanoJuris engineering`
Data: `2026-08-20`

## Objective

Promote only candidate surfaces whose local evidence supports a reproducible
contract. Keep catalog metadata separate from decision search.

## Requirements

- RF-001: expose SJUR/TSE public metadata catalogs through a runtime adapter.
- RF-002: preserve raw catalog objects, tribunal payload and source trace.
- RF-003: keep SJUR/TSE decision search outside unified search.
- RF-004: require success, schema-change, access-control and source-unavailable
  tests for the catalog adapter.
- RF-005: keep TJMG, TJRN and TRF3 pending until result fixtures exist.

## Acceptance criteria

- AC-001: SJUR/TSE is registered with `supports_catalog=true` and
  `supports_unified_search=false`.
- AC-002: all four public catalog routes map to `ProviderOption` values and raw
  payloads are preserved.
- AC-003: decision search raises an explicit unsupported error.
- AC-004: the full suite, documentation audit, coverage generation and SDD
  validation pass.
