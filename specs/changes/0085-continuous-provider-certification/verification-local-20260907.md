# Local verification - continuous provider certification

- Added `src/nanojuris/certification.py` with freshness TTL, risk-based smoke
  cadence, schema/route/selector drift detection, completeness alerts, and
  conservative promotion eligibility.
- Added `tools/build_provider_certification.py` and generated
  `docs/operations/provider-certification-20260907.json` plus Markdown.
- Added schema `docs/schemas/provider-certification-v1.schema.json`.
- The certification manifest consumes the existing technical promotion
  manifest as a separate gate; freshness/completeness cannot override a failed
  technical gate.
- `tests/test_certification.py`: 7 passed.
- Catalog manifest: 64 providers observed, 0 technically promotable because
  the current catalog lacks measured completeness for every entry. This is an
  intentional conservative result, not a failure converted to empty.

Shadow comparison and parser rollback are covered by the existing governance
module and new rollback decision tests; this module does not mutate runtime
registration or deployment state.
