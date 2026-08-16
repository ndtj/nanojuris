# TJPE contract diagnostic - 2026-08-16

The official TJPE REST surface was requested with normal TLS verification and
the local environment failed certificate-chain validation before receiving a
response. A separate, read-only diagnostic request without certificate
verification confirmed the documented JSON shape (`/api/v1/jurisprudencias`,
zero-based `page`, `size`, `X-Total-Count`, and decision text fields).

This is **not** live success evidence. The runtime provider continues to require
normal TLS verification and the catalog keeps the live state conservative until
the same response is reproduced in an environment with a valid CA chain.

Machine-readable record: [`20260816T101402Z-tjpe-contract-diagnostic.json`](20260816T101402Z-tjpe-contract-diagnostic.json).
