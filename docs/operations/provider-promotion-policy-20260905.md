# Provider promotion policy

This policy is the local decision baseline for the current development cycle.
It is intentionally conservative and does not authorize deployment or release.

The technical part of this decision is automated by
`python tools/build_promotion_manifest.py --write`. For this local cycle, the
operator accepted every source that passes all technical gates; the manifest
therefore enables those sources automatically. This is a project operating
decision only and does not authorize deployment or redistribution.
The operator also decided that an additional internal license or judicial-
authorization gate is not required for local/federated technical operation;
source access controls, robots/rate limits and any external restrictions remain
enforced and are never bypassed.

## Default gates

Every provider must satisfy all technical gates before federation:

- `contract_valid=true`;
- `live_validated=true`;
- `fixtures_complete=true`;
- `quality_gate_passed=true`;
- access is not blocked or unavailable.

Technical success enables local federation under the operator decision. A
source that fails any technical gate remains `opt_in` or `blocked` in the
promotion manifest. Capability-based calls may still be made explicitly (or by
the compatibility default) so that diagnostics are visible; access-controlled
responses are surfaced as failures and never converted into empty results.

## Current priority decisions

| Source | Technical disposition | Federated rollout | Reason |
|---|---|---|---|
| `tjba_graphql` | technically validated | enabled | operator accepted public-source operation; live page, empty query and public full-text evidence |
| `tjdf_juris` | technically validated | enabled | operator accepted public-source operation; live contract and canonical mapping evidence |
| `tjes_cjpg` | technically validated | enabled | operator accepted public-source operation; CJPG live evidence |
| `tjes_jurisprudencia` | technically validated | enabled | operator accepted public-source operation; CJSG live evidence |
| `tjes_turma_recursal` | technically validated | enabled | operator accepted public-source operation; separate Turma Recursal collection with live textual evidence |
| `tjal_esmal_banco_sentencas` | technically validated | enabled as partial CJPG | curated ESMAL sentence bank; live bounded evidence and `total_known=false` remain explicit |
| `tjgo_projudi_jurisprudencia` | technically validated | enabled | operator accepted public-source operation; fixture, pages 1–3, process-number filter and explicit empty evidence |
| `tjpi_juspi` | technically validated | enabled | operator accepted public-source operation; live pages, CNJ lookup, public HTML detail and explicit empty classification |
| `tjmt_jurisprudencia_api` | technically validated | enabled | operator accepted public-source operation; live API page, inline full-text extraction and explicit HTTP error handling |
| `tjpr_jurisprudencia` | technically validated | enabled | operator accepted public-source operation; live page, pagination and canonical mapping evidence |
| `tjrn_jurisprudencia` | technically validated | enabled | operator accepted public-source operation; bounded live + pagination evidence |
| `tjro_jurisprudencia` | technically validated | enabled | operator accepted public-source operation; public JSON contract, pagination and document evidence |
| `tjrs_solr` | technically validated | enabled | operator accepted public-source operation; public search contract and canonical mapping evidence |
| `tjsp_cjpg` | technically validated | enabled | operator accepted public-source operation; CJPG live evidence |
| `tjto_jurisprudencia` | technically validated | enabled | operator accepted public-source operation; live HTML search, pagination and bounded detail evidence |
| `stj_scon` | not technically ready | opt-in | live access-state evidence exists, but reproducible fixtures and quality gate are still pending |
| `tjto_cjpg` | blocked | disabled | official endpoint returned HTTP 403 |
| `tjsp_cjsg` | blocked | disabled | access-control/CAPTCHA signals |

## Explicit opt-in

An operator may explicitly opt in to a source that is not yet in the technical
promotion manifest (for example, while collecting additional evidence):

```python
from nanojuris import NanoJurisClient, NanoJurisConfig

client = NanoJurisClient(config=NanoJurisConfig(unified_opt_in_sources=("tjes_cjpg",)))
```

The default value remains empty because the technically promoted sources are
represented by their promoted capability. The current generated manifest
exposes 51 sources in the federation and keeps the remaining runtime providers
diagnostic/opt-in only; the promotion manifest
is the authoritative rollout decision and never promotes incomplete or
blocked entries. Such sources remain explicit in diagnostics and can be
exercised only by deliberate source selection when their provider contract
allows it.

## Non-decisions

- No CAPTCHA, WAF, login, TLS or rate-limit bypass is permitted.
- Juscraper remains an inventory and differential reference, not copied code.
- No provider is marked national coverage solely because an adapter exists.
- No push, publication, OCI apply or production change is authorized by this
  artifact.
