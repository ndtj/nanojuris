# NanoJuris execution handoff — final local state (2026-09-07)

Use this file as the authoritative continuation point. The worktree has no
commit, push, publication, deploy, Terraform apply, IAM change, or production
change.

## Verified implementation

- Full library suite: **1531 passed, 26 skipped**.
- Platform suite: **153 passed**; platform Ruff, format, mypy and JavaScript
  syntax checks pass.
- Ruff check, Ruff format check, mypy, compileall, git diff check, and the
  static no-AI gate all pass.
- Public lawful-access contracts are implemented in `src/nanojuris/access.py`:
  `AccessPath`, `AccessAttempt`, `AccessOutcome`, and `classify_access`.
- Access tests: **8 passed**. Passive markers, enforced challenges, 403, 429,
  redirects outside the allowlist, and redaction remain explicit states.
- The reusable boundary is in
  `docs/coverage/public-access-boundary-playbook-20260908.md` and its JSON
  companion; it permits bounded public access only and no challenge evasion.
- Coverage generator output: **27 authorities, 25 complete 8-of-8, 2 blocked
  rechecks, claim 25/27**. This is not national completion.

## Open work

- Current audit: 44 open tasks: 39 external-source tasks and five human-review
  tasks from SDDs 0089/0090. See
  `docs/coverage/open-task-audit-20260907.json`.
- `trf3_jurisprudencia` now has an opt-in exact-process adapter with offline
  fixtures; its direct live recheck timed out and remains `transport_error`.
- TJRJ EJURIS and TST were rechecked live with redacted evidence; their family
  gates remain open until all required authorities and filters are proven.
- Live tests requiring opt-in environment variables were not silently treated
  as success or empty; external blocks remain visible in diagnostics.
- The 2026-09-07 TJRJ EJURIS form inspection confirmed its public origin list
  is second-instance-only; see
  `docs/provider-discovery/tjrj-ejuris-origin-options-live-20260907.json`.
  This strengthens CJSG evidence but leaves TJRJ/CJPG open.
- The 2026-09-07 TJSE Boletim Jurídico recheck returned 10 public textual
  second-degree ementas with explicit CJSG identity; the source's cross-edition
  total remains unknown. See
  `docs/provider-discovery/tjse-boletim-jurisprudencia-live-20260907.json`.
- The pending-document batch for seven link-only/unknown sources is recorded in
  `docs/provider-discovery/document-qa-cycle-20260907-batch10.json`. It keeps
  CJF/STF access or TLS failures, SJUR catalog-only behavior, BNP HTTP 405, TJCE
  Informativos HTTP 200, and TJSP NugepNAC's explicit empty response distinct;
  no external failure was converted to an empty result.
- The new official TRT2 BASIS curated bulletin provider is implemented locally
  with a sanitized fixture and opt-in federation contract. Its bounded evidence
  is `docs/provider-discovery/trt2-basis-live-20260907.json`; a prior HTTP 200
  observed bulletin cards, while the subsequent adapter recheck timed out, so
  it remains `partial` and is not promoted by default.

## Safe continuation order

1. Add human relevance labels to `docs/benchmarks/live-ranking-v1.json` and
   run the holdout evaluator; do not fabricate labels.
2. Execute remaining provider tasks in one-to-three-provider batches and
   regenerate all coverage outputs.
3. Execute public access only through ordinary HTTPS/browser behavior; never
   solve or evade CAPTCHA, WAF, Turnstile, login, TLS, rate limits, or access
   controls.
4. Process 0081–0085 in one-to-three-provider batches with fixtures, bounded
   live evidence, focused tests, and explicit blocked states.
5. Keep 27/27 unclaimed until every authority has all eight gates.

## Required gates

```powershell
$env:PYTHONPATH='src'
python tools/validate_sdd.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

No step in this handoff authorizes release or deployment.
