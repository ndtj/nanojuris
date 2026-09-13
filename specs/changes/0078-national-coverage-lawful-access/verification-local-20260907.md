# Local verification - national program foundation

- Baseline generators and SDD validation pass.
- Surface registry: 150 mapped, 125 required, CJPG 7/27, CJSG 25/27, one
  explicit diagnostic/runtime divergence.
- Provider capability ledger and document inventory cover all 64 catalog
  providers.
- Shared transport already supplies bounded timeout, retry, backoff, cache,
  rate-limit, redirect allowlisting, and redaction behavior.
- `nanojuris.access` and its tests preserve passive/enforced challenges and
  external error states.
- SDD 0080 supplies the integrated ephemeral session and ordinary Chromium
  lifecycle required by T007/T008; its focused tests and verification artifact
  are the evidence for these delegated tasks.
- The public session pins the shared transport to HTTP/1.1 semantics and
  `verify_ssl=True`; unsupported protocol values fail closed. This is a
  bounded fallback, not a TLS downgrade or a challenge bypass.
- Certification manifest supplies evidence TTL, smoke cadence, drift and
  completeness alerts; current missing completeness blocks promotion.
- The final local suite and national inventory audit were rerun after the
  runtime changes: 1490 library tests passed (26 opt-in skips), all coverage
  generators and SDD validation passed, and the current audit remains explicit
  at 25/27 complete CJSG workpacks and 7/27 CJPG surfaces.
- Promotion remains gate-controlled: the technical and certification manifests
  do not promote entries with missing completeness. Bounded live, freshness,
  shadow, and rollback artifacts retain external errors explicitly; no failure
  is rewritten as an empty result.

Provider closure, full differential filter proof, live documents, and external
access gates remain open and are not represented as completed here.
