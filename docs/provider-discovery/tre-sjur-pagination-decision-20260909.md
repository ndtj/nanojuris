# SJUR/TRE pagination decision — 2026-09-09

The official TRE-SP endpoint was queried once for page 1 and once for page 2
using the same bounded public request shape. Both responses returned HTTP 200,
`totalRegistros=10`, and the same ten decision identifiers in a different
order. The evidence is stored in
`tre-sp-sjur-pagination-live-20260909.json`; response bodies were not retained.

Technical decision:

- `tre_*_sjur_jurisprudencia` accepts only `page=1`;
- `page>1` raises the explicit unsupported-query error;
- a non-empty response is exposed as `total_known=false` and
  `is_complete=false`;
- repeated windows are never counted as a second page or as exhaustive
  coverage;
- the adapters remain opt-in candidates and are not added to the default
  federation or national matrix as GOLD surfaces.

No CAPTCHA, WAF, Turnstile, authentication, proxy, token or rate-limit bypass
was attempted.
