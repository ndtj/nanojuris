# TCE-PR ViaJuris transport recheck — 2026-09-08

The snapshot download now uses the shared bounded transport. It enforces the
official ViaJuris host allowlist, HTTPS/TLS verification, a 80 MB response
limit and no transparent replay of a failed large download. The parser still
distinguishes an empty CSV or schema change from transport, access and rate
limit failures.

No live body is persisted by this note. The existing bounded live evidence for
the provider remains authoritative for availability and content shape.
