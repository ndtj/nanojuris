# 0029 - TJSP SAJ standalone flow

Status: `in_progress`

## Intent

Provide a standalone TJSP CJSG public-search example that follows the same
session contract as the provider while preserving source access controls.

## Scope

- keep cookies in one in-memory session for one bounded query;
- submit the public search form and use the first-page route only when safe;
- parse result fragments and preserve `cdAcordao`/`cdForo` document links;
- classify CAPTCHA, login, empty session and malformed responses explicitly;
- include offline parser tests and live evidence.

Out of scope: CAPTCHA solving, token fabrication, control-route invocation,
cookie persistence, mass collection, or access-control bypass.

## Requirements

- REQ-001: the example must not call `captchaControleAcesso.do`.
- REQ-002: a returned CAPTCHA/control form must not become `sem_resultados`.
- REQ-003: result fragments from either POST or first-page GET must parse.
- REQ-004: the example must retain the official form action host check.
- REQ-005: docs, tests and REA evidence must describe the same behavior.

## Acceptance criteria

- AC-001: offline tests cover hidden form fields, result fragments and control responses.
- AC-002: live execution returns an explicit access-control state on the current TJSP source.
- AC-003: full project verification and CI pass.
