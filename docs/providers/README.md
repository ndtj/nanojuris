# Provider Dossiers

This is the canonical human-readable documentation tree for NanoJuris
providers and source candidates.

## Why Each Provider Has Its Own Directory

Each source has a stable identifier and a dedicated dossier:

```text
docs/providers/<source-id>/README.md
```

The README is the complete source dossier. It records the official source,
observed routes, parameters, extracted fields, response states, fixtures,
limitations, responsible-use rules, and MCP guidance. A provider is never
considered ready merely because its directory exists: its implementation
status is declared in the central registry and validated against
`src/nanojuris/providers`.

## Compatibility And Preservation

The former flat tree remains available at
`docs/source-contracts/<source-id>.md`. The files were copied byte-for-byte
into this tree before the migration. They are retained as compatibility paths
for existing links, bookmarks, issue references, and external agents.

The documentation test suite compares every canonical README with its legacy
counterpart. A content change must therefore be made in both locations until
the compatibility layer is intentionally retired in a versioned migration.
This rule prevents a provider contract, limitation, fixture note, or warning
from disappearing during the transition.

## Reading Order

For a human:

1. Read this index and the source-specific README.
2. Check the status in `../registry/providers.json`.
3. Compare operational maturity with `nanojuris contratos --fonte <source-id>`.
4. Read the queue and national coverage matrix before planning a new provider.

For an AI agent:

1. Load `../registry/providers.json`.
2. Resolve `human_doc` to the provider README.
3. If `status` is `implemented`, call `list_sources` and `source_contracts`
   before searching.
4. If `status` is `candidate`, treat the dossier as research evidence, not as
   an available provider.
5. Preserve `searched_sources`, `skipped_sources`, `errors`, and source traces
   in the answer.

## Current Maturity

The current snapshot contains 57 dossiers: 34 implemented sources, 22
research candidates, and one shared eproc family specification. The detailed
state is maintained by the
[provider documentation audit](../provider-documentation-audit.md).

The audit intentionally exposes incomplete contracts. In particular, a
candidate may have a confirmed official route while still lacking a stable
fixture, empty-result behavior, document route, or parser contract. An
implemented provider may also remain below agent-ready maturity when the
source has access controls or an unstable public interface.

The initial controlled real-source baseline is recorded in
[`../live-validation-2026-08-11.md`](../live-validation-2026-08-11.md). The
current implementation and unified-search checks are recorded separately in
[`../implementation-live-validation-2026-08-11.md`](../implementation-live-validation-2026-08-11.md)
and [`../unified-search-live-validation-2026-08-11.md`](../unified-search-live-validation-2026-08-11.md).
All are evidence for the date and network used, not a permanent availability
guarantee.

The candidate-source validation is recorded separately in
[`../candidate-live-validation-2026-08-11.md`](../candidate-live-validation-2026-08-11.md).
It distinguishes search data, public catalogs, documentary pages, and
access-control evidence; its historical snapshot must not be read as runtime
availability for every current candidate.

The deeper provider contract validation from 2026-08-12 is recorded in
[`../provider-contract-validation-2026-08-12.md`](../provider-contract-validation-2026-08-12.md).
It records live evidence and the boundary between an observed source route and
an adapter contract already exposed by NanoJuris.

The current Ouro quality gate and its controlled unified-search evidence are
described in [`../gold-maturity.md`](../gold-maturity.md) and
[`../unified-search-live-validation-2026-08-12.md`](../unified-search-live-validation-2026-08-12.md).

The latest provider discovery round is recorded in
[`../provider-discovery-2026-08-12.md`](../provider-discovery-2026-08-12.md).

## Dossier Contract

Every dossier must keep these topics, even when the answer is "not observed":

- identity and official ownership;
- public access status and responsible-use boundary;
- HTTP routes, methods, payloads, parameters, pagination, and limits;
- canonical fields and fields that are unstable or unavailable;
- success, empty, error, timeout, and access-control behavior;
- fixtures and evidence, without personal cookies, tokens, or secrets;
- MCP recommendation and safe user-facing explanation;
- open gaps and the next promotion step.

The machine-readable inventory is in
[`../registry/providers.json`](../registry/providers.json). The runtime
capability contract remains exposed by Python, CLI, and MCP; the registry does
not duplicate or silently replace that runtime source of truth.

The normative structure for new or deeply revised dossiers is
[`../provider-dossier-template.md`](../provider-dossier-template.md). The
current completeness matrix is generated in
[`../provider-documentation-audit.md`](../provider-documentation-audit.md).
Those artifacts distinguish a route observed in a frontend or HAR, a route
reproduced with a public HTTP response and fixture, and a provider ready for
runtime and MCP routing. An open checklist is an honest development gate, not
a missing description.
