# First-degree route inventory decision — 2026-09-09

The bounded discovery sweep queried one official homepage for each of the 27
state courts and inspected at most two same-origin scripts per homepage. It
persisted route metadata and hashes only; no response body or user data was
stored.

Current result: 19 CJPG surfaces remain without a degree-specific runtime
provider. The sweep found official candidate links on several courts, including
the TJMG sentence route, but a link or form is not a jurisprudence contract.
The TJMG query was separately probed and returned HTTP 401 with an access-code/
CAPTCHA page; it remains blocked and is not counted as CJPG coverage.

Authoritative artifacts:

- `first-degree-route-inventory-20260909.json`
- `tjmg-cjpg-legacy-live-20260909.json`

Decision: keep all providerless CJPG surfaces in `discovery_pending` or an
explicit external-blocked state until a public result route, fixtures,
canonical parser, bounded live check and federated smoke pass. No CAPTCHA,
WAF, Turnstile, authentication, proxy or token bypass was attempted.
