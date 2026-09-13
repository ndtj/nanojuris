# NanoJuris executor handoff - 2026-09-07

For a self-contained handoff intended for a follow-up model, use
docs/coverage/executor-packet-20260907.md and its machine-readable companion
docs/coverage/executor-packet-20260907.json. This file remains the detailed
current-state record.

This handoff is the current local state for a follow-up engineering model. It
does not authorize commit, push, release, OCI changes, or deployment.

## Verified local state

- Library suite: 1531 passed, 26 opt-in skips.
- SDD validator, Ruff, format check, mypy, compileall, and diff check pass.
- Coverage program: 27 authorities, 25/27 complete eight-gate appellate
  workpacks, 2 blocked rechecks; CJPG 7/27 and CJSG 25/27.
- Surface registry: 150 mapped surfaces, 125 required, one explicit
  diagnostic/runtime divergence. A blocked or unobserved source is never
  counted as an empty result.
- Provider certification: 67 catalog providers, 62 runtime, zero promotable
  without measured completeness. This conservative result is intentional.
- Public access runtime: ephemeral allowlisted session, in-memory CSRF
  extraction, ordinary Playwright Chromium lifecycle, bounded shared transport,
  HTTP/1.1 only, TLS verification required, and no stealth or challenge solver.
- Ranking smoke: six benchmark queries ran against `cnj_jurisprudencia`; the
  redacted artifact is
  `docs/benchmarks/live-ranking-smoke-20260907.json`.
- A second local performance run used 1,000 rounds over 240 candidates and
  measured p95 78,125 ms of CPU process time with zero network calls;
  `docs/benchmarks/live-ranking-performance-20260907-cycle2.json`.
- TJRJ EJURIS was rechecked live with a bounded public form/XHR flow. The
  redacted evidence is `docs/provider-discovery/tjrj-ejuris-live-20260907-redacted.json`;
  the result is second-degree, HTTP 200, with no hidden ASP.NET state or CAPTCHA
  response retained in `SourceTrace`.
- TST was rechecked live through search and detail. The redacted evidence is
  `docs/provider-discovery/tst-live-20260907-current.json`; family-level labor
  promotion remains open until TRT/TST differential gates are complete.
- TST filter/pagination semantics are now explicit in `SearchPage`; the live
  differential artifact is
  `docs/provider-discovery/tst-differential-live-20260907.json`.
- TRF3 now has an opt-in exact-process adapter with offline fixtures. Its direct
  bounded recheck timed out and remains `transport_error`; it is not in the
  default federation.
- The client single-source boundary now fills missing active filter
  dispositions from declared capabilities without overriding provider traces;
  unsupported and unverified filters remain explicit.
- TJPR's public detail/document route was rechecked with a pending-content
  result and a reachable official HTML document; evidence is
  `docs/provider-discovery/document-qa-tjpr-20260907.json`.
- TJRJ's official EJURIS form was inspected again; its origin options confirm
  second-instance scope and expose no first-degree option. Evidence is
  `docs/provider-discovery/tjrj-ejuris-origin-options-live-20260907.json`.
- TJSE's public Boletim Jurídico was revalidated with a bounded public query;
  10 ementas were returned from an appellate section with explicit second-
  degree identity and unknown cross-edition total. Evidence is
  `docs/provider-discovery/tjse-boletim-jurisprudencia-live-20260907.json`.
- The pending-document batch for seven declared link-only/unknown sources is
  `docs/provider-discovery/document-qa-cycle-20260907-batch10.json`; it keeps
  BNP HTTP 405, CJF/STF access or TLS failures, SJUR catalog-only behavior,
  TJCE Informativos HTTP 200, and TJSP NugepNAC's explicit empty response
  distinct.

## Open work, classified honestly

The remaining unchecked SDD tasks are not interchangeable. They require one of
the following kinds of evidence:

1. **External public source evidence** - a bounded official route, successful
   response, pagination, filters, detail/document route, and sanitized fixture.
   This includes the unresolved TJAP/TJMA challenge-protected routes, the
   remaining state CJPG/CJSG surfaces, labor/electoral families, and federal,
   superior, and military surfaces.
2. **Human review** - relevance labels and holdout calibration for ranking,
   legal/retention decisions, or an operator decision that is outside code.
3. **Provider-specific differential work** - filters, degree, identity, and
   document links cannot be marked complete from a catalog declaration alone.

Use the task files as the authoritative checklist. The current unchecked count
is generated with:

```powershell
$rows = Get-ChildItem specs/changes -Recurse -Filter tasks.md | ForEach-Object {
  $lines = Get-Content $_.FullName
  [pscustomobject]@{
    Path = $_.FullName
    Open = @($lines | Where-Object { $_ -match '^\s*- \[ \]' }).Count
  }
}
$rows | Where-Object Open -gt 0
```

The machine-readable classification is in
`docs/coverage/open-task-audit-20260907.json` and can be regenerated with
`python tools/audit_open_tasks.py`. The current classification is 44 open tasks:
39 external-source tasks and five human-review tasks from
SDDs 0089/0090 (the consolidated handoff plan). The immutable pre-change baseline was
reconstructed and recorded in
`docs/benchmarks/live-ranking-baseline-20260907.json`.

Do not mark an external or human gate as passed merely because an adapter,
HTTP 200 shell, catalog row, or contextual result exists.

## Safe continuation order

1. Re-run the generators and record their hashes.
2. Work in one to three providers at a time, using only official public routes.
3. Use `src/nanojuris/access.py` and `src/nanojuris/public_access.py` for
   bounded access; classify 403, 429, CAPTCHA, WAF, TLS, timeout, and schema
   drift explicitly.
4. Add sanitized success/empty/error/drift fixtures and differential tests.
5. Promote only when runtime, degree contract, fixtures, bounded live evidence,
   quality, and federation gates all pass.
6. Keep challenge-protected surfaces outside the federation until the source
   offers a normal public path. Never use stealth, solver/OCR, token replay,
   fingerprint spoofing, proxy rotation, TLS relaxation, or rate-limit evasion.
7. Apply `docs/coverage/public-access-boundary-playbook-20260908.md` for the
   allowed/prohibited technique matrix and human-mediated challenge rule.

## Reproducibility commands

```powershell
cd C:\Users\admin\Desktop\Nanojuris\repos\nanojuris
$env:PYTHONPATH = 'src'
python tools/audit_provider_docs.py --write
python tools/build_provider_coverage.py --write
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/build_provider_certification.py
python tools/validate_sdd.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

## Stop conditions

The local implementation is healthy, but national coverage is not complete:
the current claim is 25/27 appellate workpacks, not 27/27. Continue only when
new official evidence is available; otherwise produce a blocker report with
the URL, timestamp, bounded method, redacted response classification, and the
official action needed. No production mutation has been made.
