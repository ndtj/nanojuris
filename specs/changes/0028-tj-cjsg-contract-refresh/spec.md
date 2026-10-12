# 0028 - TJ CJSG contract refresh

Status: `in_progress`

## Intent

Align the CJSG/e-SAJ provider metadata with the public form route observed by
REA, without changing extraction behavior or access-control handling.

## Scope

- declare `GET /consultaCompleta.do` for the observed CJSG family providers;
- keep CAPTCHA, login, WAF, robots, rate-limit and source-unavailable states explicit;
- update canonical provider dossiers, tests and generated catalogs;
- preserve the bounded discovery evidence.

Out of scope: CAPTCHA or WAF bypass, token fabrication, cookie reuse, guessed
POST submissions, mass collection, or new adapters.

## Requirements

- REQ-001: TJAC, TJAL, TJMS and TJSP declare the observed public form route.
- REQ-002: the shared TJCE contract remains marked as unverified when robots
  prevents live confirmation.
- REQ-003: TJAM and TJCE are not claimed live-verified by this change.
- REQ-004: tests, documentation and generated catalogs agree with capabilities.
- REQ-005: no access-control bypass is introduced.

## Acceptance criteria

- AC-001: route declarations exist in the four observed adapters and inherited
  TJCE metadata is documented as not live-confirmed.
- AC-002: bounded CJSG discovery records the evidence and its limitations.
- AC-003: targeted and full tests, lint, type checking, build and SDD validation pass.
