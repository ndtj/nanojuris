# Shared transport hardening — cycle 2026-09-08

## Scope

Three public providers were moved from provider-local HTTP execution to the
bounded `SharedHttpClient` boundary:

- `tce_pr_viajuris` — annual ViaJuris CSV snapshot;
- `tjmg_jurisprudencia` — modern public API, document route and legacy form
  diagnostic fallback;
- `tjmg_dspace_jurisprudencia` — public DSpace search, item metadata, bundles,
  bitstreams and document content.
- `trt2_basis_jurisprudencia` — public BASIS DSpace bulletin search and PDF
  detail; the provider remains opt-in because the collection is curated.
- `trt15_jurisprudencia` — public catalog/search/detail API; the provider
  remains outside federation because the search endpoint requires CAPTCHA.
- `tjrj_banco_sentencas` — official selected-sentence PDF index; the provider
  remains curated and opt-in rather than a complete CJPG source.

## Safety decisions

- Official HTTPS host allowlists remain provider-specific.
- Response byte limits are enforced before parsers receive bodies.
- Redirects and TLS verification are controlled by the shared policy.
- Stateful or large requests use zero automatic retries; callers preserve the
  distinction between timeout, transport failure, access control, rate limit,
  schema drift and an authoritative empty result.
- No CAPTCHA, WAF, Turnstile, login or TLS control was bypassed.
- Response bodies are not persisted by the recheck artifacts; only bounded
  hashes and metadata are recorded.

## Verification

- Focused provider/documentation tests: 84 passed in the first batch and 25
  passed in the follow-up batch (including the TRT2 BASIS migration).
- Full suite: 1610 passed, 26 skipped (opt-in live/optional dependency tests).
- Ruff, format check, mypy, compileall, SDD validation and `git diff --check`:
  passed.
- TJMG modern API bounded live check: HTTP 200, two records, reported total
  1000, JSON body 2691 bytes; see the live recheck artifact.
- TRT15 focused boundary suite: 11 passed; CAPTCHA, 403, 429, transport and
  parser states remain explicit and are not converted to empty results.
- TJRJ selected-sentence index suite: 8 passed after moving the bounded PDF
  request to `SharedHttpClient`; the curated scope remains explicit.

No commit, push, tag, publication, deploy, Terraform apply or production change
was performed.
