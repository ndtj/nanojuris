# Verification

Status: `verified_local`

## Resultados

```text
TRT2 shell/options: HTTP 200
TRT2 documents: challenge response; no documents collected
TJES current portal: HTTP 503
TJES legacy result route: HTTP 404
canonical/legacy dossier parity: passed
python tools/validate_sdd.py: passed
```

No adapter, fixture or deployment was added because the result contracts were
not reproducible without an access-control challenge or unavailable endpoint.

## Results

Both candidates remain documented research candidates. The audit prevents an
unsupported parser from silently returning incomplete or stale jurisprudence.

## Rastreabilidade

| Requirement | Evidence | Status |
| --- | --- | --- |
| REQ-001 | TRT2 official endpoint probes | passed |
| REQ-002 | TJES official endpoint probes | passed |
| REQ-003 | runtime/catalog inspection | passed |
