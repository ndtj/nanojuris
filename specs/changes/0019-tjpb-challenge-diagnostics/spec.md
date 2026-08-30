# 0019 - TJPB challenge diagnostics

Status: verified

## Intent

Classify the TJPB public challenge page explicitly when it replaces the CSRF
token page, instead of reporting a parser contract change.

## Requirements and acceptance

- REQ-001: detect only challenge markers in the token acquisition response.
- REQ-002: raise `AccessControlRequiredError` for a challenge page.
- REQ-003: preserve `ParserContractChangedError` for ordinary schema changes.
- REQ-004: do not solve, bypass or persist challenge data.
- AC-001: sanitized challenge fixture is classified as access control.
- AC-002: valid token flow remains compatible.
