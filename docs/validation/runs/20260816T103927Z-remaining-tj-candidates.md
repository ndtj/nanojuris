# Remaining state candidate audit

Date: 2026-08-16 10:39 UTC

The audit used public GET requests over normal TLS, with no credentials,
personal cookies, challenge solving, or access-control bypass.

| Source | Evidence | Correct classification |
| --- | --- | --- |
| `tjap_tucujuris` | Official Tucujuris entry returned HTTP 403. | Candidate blocked/inconclusive; no provider. |
| `tjes_jurisprudencia` | Current portal returned HTTP 503; legacy ColdFusion search returned HTTP 404. | Candidate surface changed/unavailable; no provider. |
| `tjma_jurisconsult` | Metadata routes returned JSON HTTP 200. Search route returned HTTP 400 when challenge/token parameters were empty. | Candidate for a future metadata/precedent adapter; not a textual decision provider yet. |
| `tjro_liame` | LIAME returned HTTP 200 and is scoped to qualified precedents/catalog data. | Contextual precedent catalog; do not present as general TJRO jurisprudence search. |

## Decision

No new textual-jurisprudence provider was safely implementable from this
round. TJMA is the strongest next candidate, but the next implementation must
choose an explicit `CanonicalPrecedent`/catalog scope or wait for a permitted
result response from the protected search route.
