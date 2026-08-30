# 0017 - TST public filter catalogs

Status: verified

## Intent

Expose the six public TST jurisprudence filter routes through the existing
`tst_jurisprudencia` provider. Search and document behavior remain unchanged.

## Scope

- retrieve JSON catalogs for judging bodies, ministers, convocados, classes,
  indicators and subjects;
- normalize explicit identifiers and labels into `ProviderOption`;
- preserve each response envelope in `ProviderCatalog.raw` and attach a
  `SourceTrace`;
- classify a non-JSON catalog response as a parser contract change.

The change does not add procedural lookup, authentication, scraping, or new
provider identities.

## Requirements

- REQ-001: Call only the six documented public GET routes.
- REQ-002: Never invent an option identifier or label.
- REQ-003: Preserve raw public responses for auditability.
- REQ-004: Keep existing search and document APIs backward compatible.

## Acceptance criteria

- AC-001: `get_catalog()` returns a TST court option and grouped options.
- AC-002: Common list envelopes (`content`, `data`, `items`, `results`,
  `registros`) are normalized without losing raw payloads.
- AC-003: A non-JSON response raises `ParserContractChangedError`.
- AC-004: Existing provider tests and quality gates pass.
