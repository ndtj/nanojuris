# TJCE/CJSG contract diagnostic

- Source: `tjce_cjsg`
- Scope: `candidate_contract_diagnostic`
- Checked at: `2026-08-16T10:30:00Z`
- Endpoint: `GET https://esaj.tjce.jus.br/cjsg/resultadoCompleta.do`
- Result: connection reset before an HTTP response

This run records a transport limitation only. It does not classify the source
as empty, does not validate the TJCE form payload, and does not promote the
provider to live-validated or Gold. The offline provider remains useful for
regression tests of the shared e-SAJ/CJSG parser until a clean TJCE request and
result fixture are available.
