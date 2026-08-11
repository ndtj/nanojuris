# Provider Registry

The registry is the machine-readable entry point for humans, documentation
tools, CI, and AI agents that need to discover NanoJuris sources.

- [`providers.json`](providers.json) lists every documented source and separates
  implemented providers, research candidates, and shared implementation
  families.
- [`provider-schema.json`](provider-schema.json) describes the registry shape.
- The canonical human dossier is always
  `docs/providers/<source-id>/README.md`.
- `docs/source-contracts/<source-id>.md` is retained as a legacy compatibility
  path and must remain content-equivalent during the migration period.

The registry intentionally does not invent HTTP fields that are not verified.
For implemented sources, the authoritative operational contract is still
`ProviderCapabilities`, available through:

```bash
nanojuris fontes --fonte <source-id>
nanojuris contratos --fonte <source-id>
```

This separation prevents documentation metadata from becoming a stale shadow
implementation. A future contract promotion can add endpoint-level JSON files
under the provider directory after fixtures and evidence are available.
