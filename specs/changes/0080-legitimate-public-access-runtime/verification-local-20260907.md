# Verification — lawful access runtime

## Evidence

- `src/nanojuris/access.py` implements `AccessPath`, `AccessAttempt`,
  `AccessOutcome` and `classify_access` with HTTPS host allowlisting, bounded
  budgets, passive-marker versus enforced-challenge classification, and safe
  serialization.
- `tests/test_access.py`: six tests passed, covering passive markers, enforced
  challenges, HTTP 403/429, redirect allowlists, and redaction.
- `python -m ruff check src/nanojuris/access.py tests/test_access.py` passed.
- `python -m mypy src` passed.
- `src/nanojuris/public_access.py` adds an ephemeral allowlisted session,
  in-memory CSRF extraction, bounded shared transport, and ordinary Chromium
  lifecycle. `tests/test_public_access.py` and the access/certification focused
  tests pass (31 tests total).
- HTTP/1.1 is explicit in `TransportPolicy`; TLS verification remains enabled
  and redirects remain host-allowlisted. No stealth, proxy rotation, solver,
  or challenge-token handling is present.

This closes local modeling and classification work. Public browser sessions,
live calls and external availability remain separate verification gates; no
CAPTCHA, WAF, Turnstile or other access control is bypassed.
