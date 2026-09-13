# Verification

## Resultados

The Falcao catalog row remains a candidate without a runtime binding. The
SJUR/TSE adapter is explicitly catalog-only and raises an unsupported-query
state for decision search; catalog metadata is therefore not counted as
electoral jurisprudence. The generated promotion manifest and federation tests
keep unapproved surfaces out of the rollout.

TRT/TST bindings and differential fixtures remain open until an official
textual decision route is reproduced with authority, pagination, and fields.

The TST adapter now exposes `total_known`, explicit public extraction/access
states, and native versus unsupported filter dispositions in `SearchPage`.
Bounded live differential evidence for page 1, page 2, exact phrase, and
excluded terms is recorded in
`docs/provider-discovery/tst-differential-live-20260907.json`; page 1 and page
2 had no overlap. This closes the TST-side local contract gap but does not
close the TRT/TST family gate while the TRT route remains without a
reproducible result contract.

The public TST filter catalog was also queried through the adapter and recorded
without response bodies in
`docs/provider-discovery/tst-catalog-live-20260907.json` (HTTP 200; six public
catalog routes). Fixture coverage for the catalog envelope is in
`tests/test_tst_jurisprudencia.py`.

## Rastreabilidade

AC-001 -> T001-T002; AC-002 -> T003; AC-003 -> T002-T004; AC-004 -> T004-T006.

## Evidence update 2026-09-07

The bounded public TST smoke completed successfully and is recorded in
`docs/provider-discovery/tst-live-20260907-current.json`: the official search
returned one textual result over HTTP 200 and the linked detail route returned
HTML with non-empty text. The broader T002/T004 gates remain open because TRT
and TST authority coverage, differential fixtures, and filter evidence must be
closed as a family; the TST result alone is not promoted as national labor
coverage.

The same TST flow was rerun on 2026-09-07 with the bounded smoke command;
`docs/provider-discovery/tst-live-20260907-cycle60.json` records HTTP 200,
one result, and a non-empty HTML detail. This is additional TST evidence only;
it does not change the unresolved TRT external contract.
