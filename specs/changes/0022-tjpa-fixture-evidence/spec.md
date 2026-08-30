# 0022 - TJPA versioned fixture evidence

Status: verified

## Requirements and acceptance

- REQ-001: keep a small sanitized JSON success envelope for the public TJPA search route.
- REQ-002: parse the fixture through the same canonical parser used by the runtime provider.
- REQ-003: retain normalized dates, raw dates, identifiers and public full text.
- AC-001: the versioned fixture contract test passes offline.
- AC-002: no production endpoint or credential is used by the test.
