# 0020 - TCE-PR ViaJuris CSV

Status: verified

## Requirements

- REQ-001: download only the official annual ViaJuris CSV route.
- REQ-002: parse semicolon CSV with Brazilian encodings and explicit identity.
- REQ-003: normalize jurisprudence fields and preserve `UrlPDF` safely.
- REQ-004: expose a no-download year catalog and classified failures.

## Acceptance

- AC-001: sanitized fixture yields searchable canonical results.
- AC-002: dates and official PDF links are normalized safely.
- AC-003: missing identifier schema and HTTP failures are explicit.
- AC-004: provider is registered and quality tests pass.
