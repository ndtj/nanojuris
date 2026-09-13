# Design - national surface state registry

`tools/build_surface_state_registry.py` joins the generated degree matrix with
the generated provider catalog, promotion manifest, and operator approval
artifacts. Its stable key is `authority + degree + collection + provider`
through the generated `surface_id`.

The projection preserves independent dimensions:

```text
lifecycle
contract_status
live_status
federation_status
legal_status
document_capability
evidence_ids
```

The generator also emits `divergences` for a provider missing from the catalog,
simultaneous runtime/diagnostic bindings, or diagnostic evidence without a
runtime binding. No row is promoted because a route name happens to exist.

Generated JSON and Markdown are outputs, not hand-edited sources. Re-run the
generator after catalog or live-evidence changes.
