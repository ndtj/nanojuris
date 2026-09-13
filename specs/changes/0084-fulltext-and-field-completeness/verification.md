# Verificação

## Resultados

Planejamento criado; nenhum provider recebeu selo ouro por declaração.

The client search boundary now fills missing active-filter dispositions from
the provider capability contract without overriding provider-supplied values.
This makes unsupported, native, translated, validated-scope, and unverified
states visible even for legacy adapters that return an otherwise valid page.
Focused coverage is in `tests/test_audit_regressions.py`, and the TST/TJPR
adapters additionally expose explicit total, access, extraction, and filter
metadata.
The TJPR document route was rechecked live on 2026-09-07 with an official HTML
detail URL, non-empty extracted text, MIME validation and no probe failure; the
redacted evidence is `docs/provider-discovery/document-qa-tjpr-20260907.json`.

A second bounded document-QA batch on 2026-09-07 checked TRF5, STM, TST and
TJPR through the normal public routes. All four searches returned a candidate,
all four detail calls extracted non-empty text, and all public URLs returned
HTTP 200 without probe failures. The redacted aggregate is
`docs/provider-discovery/document-qa-cycle-20260907-batch06.json`. This closes
the evidence gap only for those four surfaces; T019/T004/T005 remain open for
the remaining providers and document formats.

The shared document boundary was hardened locally on 2026-09-07. `DocumentReference`
can retain an explicit `decision_id`; `fetch_document_reference` passes the
transport byte limit into `build_canonical_document`; and canonical metadata
now records deterministic SHA-256, size, MIME/PDF structural status, page
count, and an explicit decision-document relation when supplied by a provider.
A mismatching pre-existing trace hash is corrected to the hash of the bytes
actually validated. The diagnostic URL probe in
`tools/qa_jurisprudence_documents.py` now enforces HTTPS/same-host redirects,
streams at most 4 MB, computes a redacted hash and reports malformed, empty,
and over-sized documents explicitly. It never turns a transport or access
error into an empty result.

Verification commands:

```text
python -m pytest -q tests/test_documents.py tests/test_transport_runtime.py tests/test_fixture_quality_audit.py
36 passed
python -m ruff check src/nanojuris/documents.py tools/qa_jurisprudence_documents.py tests/test_documents.py
python -m ruff format --check src/nanojuris/documents.py tools/qa_jurisprudence_documents.py tests/test_documents.py
python -m mypy src/nanojuris/documents.py tools/qa_jurisprudence_documents.py
```

This is a reusable local gate, not proof that all 64 providers expose a
retrievable document. The family-wide external task remains open until each
provider has a bounded live response and a sanitized fixture covering its
document route.

One post-change bounded live probe of `trf5_jurisprudencia` (query
`responsabilidade civil`) returned one result, loaded 9,941 bytes of public
HTML, extracted 9,941 characters, and reached the official document URL with
HTTP 200. The probe reported `status=valid`, matching MIME, a SHA-256 and no
document failure in
`docs/provider-discovery/document-qa-cycle-20260907-batch08.json`.

The next bounded pending-document batch covered all seven runtime sources that
still declare a link-only, unknown, or unavailable detail route. BNP's search
result was contextual and its search URL correctly returned HTTP 405; CJF and
the two STF surfaces retained explicit access/TLS errors; SJUR/TSE retained
its catalog-only contract; TJCE Informativos reached an official HTML page at
HTTP 200; and TJSP NugepNAC returned an explicit zero-result response for the
term used. The redacted aggregate is
`docs/provider-discovery/document-qa-cycle-20260907-batch10.json`. These
outcomes improve the ledger but do not close the family-wide T019/T004/T005
gates; no external error was classified as an authoritative empty result.

## Rastreabilidade

AC-001 → T001–T002; AC-002 → T002–T003; AC-003 → T004–T005; AC-004 → T006.
