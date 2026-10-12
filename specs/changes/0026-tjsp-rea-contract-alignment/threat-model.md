# Threat model — TJSP public jurisprudence adapters

This change is about a public web source that may impose CAPTCHA, login, WAF,
rate-limit and session controls.

## Assets

- integrity of canonical jurisprudence records;
- provenance and raw response evidence;
- source availability and user credentials (which must never enter the repo).

## Threats and controls

| Threat | Control |
| --- | --- |
| CAPTCHA bypass disguised as automation | detect and raise `AccessControlRequiredError` |
| login page mistaken for a decision | classify verification/login HTML and preserve warnings |
| stale hidden fields used for pagination | serialize only the current public result form |
| source layout drift | parser contract errors, fixtures and docs audit |
| accidental bulk collection | bounded tests, configured rate limit, no crawl loop |
| secret leakage | no credentials/tokens in payloads, fixtures or Git |

The design does not introduce authentication, token replay, browser-cookie
reuse or evasion of source controls.
