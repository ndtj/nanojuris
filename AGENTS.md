# AGENTS.md

This file is the operational entry point for AI coding agents working on
NanoJuris.

## Product Boundary

NanoJuris is for public Brazilian jurisprudence, precedents, decisions,
informativos, public full text when available, canonical records, provenance and
jurimetry.

Do not add procedural case lookup, court communications, DJEN, DataJud,
movements, parties or procedural timelines here. Those belong to NanoJud.

## Canonical Discovery Order

Before changing or using a provider, read these files in order:

1. `docs/coverage/README.md`
2. `docs/registry/provider-catalog.full.json`
3. `docs/providers/<source_id>/README.md`
4. `docs/source-contracts/<source_id>.md`
5. `src/nanojuris/providers/<source_id>.py`
6. Related fixtures and tests under `tests/`

The machine-readable catalog is generated. Do not edit
`docs/registry/provider-catalog.full.json` or files under `docs/coverage/`
manually. Update runtime declarations, provider dossiers or the generator, then
run:

```bash
python tools/build_provider_coverage.py --write
```

## Provider Quality Rules

A provider is not mature because an endpoint responded once. A mature provider
must document:

- official source and public entry point;
- search inputs, filters, pagination and ordering;
- HTTP routes, methods, payloads and response types;
- success, empty result, invalid query, access control, rate limit, timeout and
  source change behavior;
- canonical fields and raw fields;
- public fixtures for parser tests;
- full text/document behavior when available;
- source trace and extraction trace expectations;
- MCP/Studio/CLI exposure decisions.

Never classify CAPTCHA, WAF, login, TLS reset or timeout as zero results.

## Jurimetry Standard

For statistical jurisprudence research, prefer providers with:

- `coverage_role=primary_textual_jurisprudence`;
- `maturity_tier=gold` or `silver`;
- `interfaces.unified_search=true`;
- canonical `CanonicalDecision` output;
- stable identity fields;
- textual legal content;
- date fields or raw date preservation;
- source trace and completeness information.

Use context providers for enrichment, not as a replacement for broad textual
jurisprudence.

## Documentation Synchronization

When a provider changes, update all relevant layers:

- `ProviderCapabilities` in code;
- source contract assessment if maturity/risk changed;
- canonical dossier in `docs/providers/<source_id>/README.md`;
- compatibility copy in `docs/source-contracts/<source_id>.md`;
- fixtures and tests;
- generated coverage catalog.

Run at least:

```bash
python tools/audit_provider_docs.py --write
python tools/build_provider_coverage.py --write
pytest tests/test_provider_documentation.py tests/test_provider_coverage.py
```

For a conservative documentation cleanup, generate the inventory before moving
or deleting anything:

```bash
python tools/audit_documentation_inventory.py --write
```

## Responsible Use

NanoJuris must not bypass CAPTCHA, WAF, login, rate limits, secrecy restrictions
or access controls. The correct behavior is explicit diagnosis with provenance,
not silent omission.
