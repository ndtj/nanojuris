# Verification

## Resultados

The provider workpack generator was rerun for the complete catalog. The
2026-09-06 bounded federated smoke rechecked 42 technical sources and
preserved CNJ HTTP 503 and TST HTTP 400 as explicit errors. The promotion
manifest remains the only federation input, so sources without a valid
contract or quality gate are not promoted.

Official alternatives and detail/document routes for the remaining federal and
superior surfaces were rechecked in
`docs/provider-discovery/blocked-route-recheck-20260907.json` and
`docs/provider-discovery/official-alternative-surface-recheck-20260907.json`.
The routes that remain challenge-protected are explicitly blocked; detail and
document contracts still require bounded live evidence and remain open.

The TST detail route was independently rechecked on 2026-09-07 by
`tools/run_tst_live_smoke.py`; the redacted result is
`docs/provider-discovery/tst-live-20260907-current.json`. It confirms one
public HTML document with non-empty extracted text, while the family-level
detail/document task remains open until all covered authorities have equivalent
evidence.

A fresh bounded run was also persisted at
`docs/provider-discovery/tst-live-20260907-cycle60.json` and is included in
the generated provider coverage inputs.

The STM and TRF4 public routes were rechecked in a bounded run on 2026-09-07
using `tools/run_stm_live_smoke.py` and `tools/run_trf4_live_smoke.py`.
The resulting evidence is `docs/provider-discovery/stm-live-20260907-cycle59.json`
and `docs/provider-discovery/trf4-live-20260907-cycle62.json`. Both observed
two non-overlapping pages, a non-empty detail document, valid extraction, and
successful HTTP responses. This closes the evidence gap for those two
surfaces only; T004 remains open for the remaining covered authorities.

TRF5 received the same bounded verification on 2026-09-07 through
`tools/run_trf5_live_smoke.py`; `docs/provider-discovery/trf5-live-20260907-cycle45.json`
records two disjoint pages and a non-empty HTML detail document. T004 remains
open for authorities without equivalent current evidence.

The shared bounded document probe then checked `tnu_eproc_jurisprudencia`,
`tjms_cjsg` and `stj_scon` on 2026-09-07. TNU returned one public HTML detail
with 29,116 extracted characters and HTTP 200; TJMS returned one public PDF,
14 pages and 41,313 extracted characters with HTTP 200; STJ/SCON preserved an
explicit `AccessControlRequiredError`. MIME, byte-size, structural PDF status
and SHA-256 were recorded without persisting the bodies in
`docs/provider-discovery/document-qa-cycle-20260907-batch09.json`. This adds
evidence for TNU/TJMS and a current access-control classification for STJ, but
does not close the family-wide T004 gate.

## Rastreabilidade

AC-001 -> T001-T002; AC-002 -> T002-T003; AC-003 -> T001/T004;
AC-004 -> T003-T005.
