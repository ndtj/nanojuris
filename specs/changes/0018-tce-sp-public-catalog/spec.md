# 0018 - TCE-SP public collection catalog

Status: verified

## Intent

Expose the two already validated, public TCE-SP jurisprudence collections as a
typed catalog while keeping the reCAPTCHA-protected search explicit.

## Requirements and acceptance

- REQ-001: call only public `sumulas` and `publicacoes` routes.
- REQ-002: return TCE-SP and the two supported species.
- REQ-003: preserve normalized records and source trace in the raw catalog.
- REQ-004: never automate or imply bypass of reCAPTCHA.
- AC-001: `get_catalog()` returns both collection counts and raw records.
- AC-002: existing search behavior remains compatible.
- AC-003: offline fixture tests pass.
