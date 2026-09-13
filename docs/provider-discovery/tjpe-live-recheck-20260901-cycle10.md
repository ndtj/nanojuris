# Rechecagem live TJPE Jurisprudencia - 2026-09-01 (ciclo 10)

Foi feita uma chamada GET publica bounded a rota REST contratada do TJPE, com
timeout de 8 s e `verify_ssl=true`. A conexao falhou antes de HTTP por
`SSLCertVerificationError`; o estado correto e `blocked_transport`.

| Rota | Resultado | Classificacao |
| --- | --- | --- |
| `GET /api/v1/jurisprudencias` | `SourceUnavailableError` por falha TLS | `blocked_transport` |

Nenhum corpo de resposta foi persistido, e o provider continua com verificacao
TLS habilitada. A fotografia nao altera o contrato nem promove a fonte.

Metadados estao em
[`tjpe-live-recheck-20260901-cycle10.json`](tjpe-live-recheck-20260901-cycle10.json).
