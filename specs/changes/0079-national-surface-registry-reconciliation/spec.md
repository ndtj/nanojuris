# 0079 - national surface state registry

Status: `verified`

## Scope

Maintain one generated registry for the current national topology. The
registry currently contains 150 mapped surfaces, 125 required surfaces, and
keeps provider, contract, live, document, legal, and federation states
independent. The projection is intentionally broader than the original
120-surface estimate because later discovery added explicit degree and family
surfaces.

## Acceptance criteria

- **AC-001:** the generator emits the current 150 mapped surfaces and 125
  required surfaces without duplicate keys.
- **AC-002:** each row contains authority, branch, degree, instance, collection,
  provider binding, lifecycle, contract, live, federation, legal, document,
  and evidence state.
- **AC-003:** catalog/runtime/live divergences are reported in the generated
  `divergences` list and are never silently corrected in generated files.
- **AC-004:** CJPG and CJSG counts are derived from explicit degree contracts,
  never from generic provider names.

## Non-goals

This SDD does not promote providers, call courts, approve legal reuse, or claim
national coverage. Blocked and unobserved sources remain explicit states.
