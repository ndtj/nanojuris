# Rechecagem live STF Jurisprudencia - 2026-09-01 (ciclo 9)

Foi feita uma chamada POST publica bounded ao endpoint JSON contratado do STF,
com `verify_ssl=true`, timeout de 8 segundos e sem credenciais. A conexao
falhou na verificacao TLS antes de receber HTTP; o estado correto e
`blocked_transport`.

| Rota | Resultado | Classificacao |
| --- | --- | --- |
| `POST /api/search/search` | `SourceUnavailableError` por `SSLError` | `blocked_transport` |

Nenhum corpo de resposta ou payload completo foi persistido. O provider segue
com verificacao TLS habilitada e nao foi promovido, rebaixado ou alterado por
esta fotografia.

Metadados estao em
[`stf-juris-live-recheck-20260901-cycle9.json`](stf-juris-live-recheck-20260901-cycle9.json).
