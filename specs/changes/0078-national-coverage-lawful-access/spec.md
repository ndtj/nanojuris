# 0078 - national coverage and lawful public access

Status: `in_progress`
Owner: Provider Engineering, Data Quality, Security, and Federation

## Objective

Create an auditable national execution model for discovering, implementing, and
certifying public jurisprudence capabilities. The current generated topology
contains 150 mapped surfaces and 125 required surfaces; the original 120-
surface estimate is retained only as historical planning context.

## Requirements

- **REQ-001:** one canonical surface exists per authority, degree, collection,
  and document scope.
- **REQ-002:** the generated registry is the denominator source; it currently
  contains 150 mapped and 125 required surfaces.
- **REQ-003:** lifecycle, contract, live, document, operation, legal, and
  federation state remain independent.
- **REQ-004:** every filter ends in a terminal classification: native,
  translated, local postfilter, unsupported, access blocked, unavailable, or
  out of scope.
- **REQ-005:** no proven filter is silently ignored.
- **REQ-006:** every observed field is canonical, raw-preserved, or explicitly
  ignored with provenance.
- **REQ-007:** document state distinguishes inline text, detail API, document
  link, public download, OCR required, not offered, and blocked.
- **REQ-008:** cookies and CSRF remain inside the normal public session only.
- **REQ-009:** CAPTCHA, WAF, login, rate limit, TLS, and schema errors never
  become an empty result.
- **REQ-010:** official alternatives are evaluated before terminal blocking.
- **REQ-011:** applicable surfaces have success, empty, error, blocked, and drift
  fixtures.
- **REQ-012:** authority, branch, degree, collection, identity, and dates are
  validated semantically.
- **REQ-013:** evidence carries observation time, temporal scope, and TTL.
- **REQ-014:** federation exposes remote, local, ignored, and unsupported
  filters per source.
- **REQ-015:** automatic technical promotion requires every technical gate and
  public access; human/legal approval remains a separate dimension.
- **REQ-016:** process data remains outside the jurisprudence boundary.
- **REQ-017:** no solver, stealth, token replay, evasive proxy, TLS downgrade,
  or exploitation is permitted.
- **REQ-018:** this program never authorizes commit, publication, or deploy.

## Acceptance criteria

- **AC-001:** generated topology and registry agree on cardinality and keys.
- **AC-002:** every catalog provider has a workpack and explicit capability
  state.
- **AC-003:** promoted providers contain no unverified filter state.
- **AC-004:** external failures remain distinct from authoritative emptiness.
- **AC-005:** observed filters have differential evidence or terminal status.
- **AC-006:** recoverable public documents have reference, hash, MIME, and link.
- **AC-007:** first-degree denominators exclude non-state process surfaces.
- **AC-008:** aggregates count only when authority and degree are proven.
- **AC-009:** no blocked source is resolved through technical evasion.
- **AC-010:** catalogs and process metadata do not count as textual decisions.
- **AC-011:** promotion follows contract, fixtures, live, quality, and federation
  gates.
- **AC-012:** verification records map requirements to commands and evidence.
- **AC-013:** suite, lint, types, compilation, and SDD validation pass.
- **AC-014:** final audit lists complete, incomplete, and blocked surfaces.
