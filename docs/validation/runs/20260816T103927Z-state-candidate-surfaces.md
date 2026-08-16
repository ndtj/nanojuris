# State candidate surface audit

Date: 2026-08-16 10:39 UTC

This run inspected public entry pages and, where available, public frontend
assets. It did not submit credentials, reuse personal cookies, solve a
challenge, or bypass access controls.

| Source | Surface | Observation | Decision |
| --- | --- | --- | --- |
| `tjmt_jurisprudencia_api` | Angular SPA + API routes in public bundle | Portal HTTP 200; API catalog and search endpoints HTTP 401 without the frontend header. The bundle points to a `hellsgate-preview` host. | Keep as candidate; do not embed the exposed frontend token or publish a runtime provider without a stable public contract. |
| `tjrn_jurisprudencia` | Portal root and JavaScript assets | Root HTTP 200 in this window; scripts returned HTTP 403. Search payload and result schema not reproduced. | Keep blocked/inconclusive; do not treat as empty. |
| `tjse_jurisprudencia` | JSF/PrimeFaces form | Form HTTP 200 with rich filters; Turnstile challenge present before a reproducible result. | Keep blocked/inconclusive; no automation around the challenge. |
| `tjmg_jurisprudencia` | RUPE portal and legacy public link | Portal HTTP 200; current surface is a RUPE portal and links to the legacy espelho form. No new result contract was obtained. | Keep candidate; inspect the legacy form only when a clean reproducible response is available. |
| `tjto_jurisprudencia` | Dedicated query page | HTTP 403 short access-denied response. | Keep candidate/block evidence; do not infer payload from indexed URLs. |

## Outcome

No candidate in this run reached the evidence threshold for a new runtime
provider. The strongest next input is a HAR from a normal, authorized browser
search for TJMT or TJRN, with cookies and tokens removed before sharing. A HAR
is only useful if it contains an actual result response, not just the landing
page.
