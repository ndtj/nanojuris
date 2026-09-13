# Rechecagem live STF Informativo - 2026-09-01

Foi feita uma rechecagem publica bounded da planilha oficial do Informativo
STF, sem credenciais e sem persistir o corpo. A verificacao TLS padrao falhou
por erro de cadeia local; a tentativa diagnostica com verificacao desabilitada
recebeu HTTP 403 e HTML curto, nao XLSX.

| Tentativa | Resultado | Classificacao |
| --- | --- | --- |
| TLS padrao (`verify_ssl=true`) | `SSLError` | `blocked_transport` |
| Diagnostica sem TLS (`verify_ssl=false`) | HTTP 403, 118 bytes | `blocked_access` |

O provider continua runtime porque ja existe contrato e evidencia live anterior,
mas esta rodada nao confirma disponibilidade atual. O 403 nao e tratado como
lista vazia e nenhum adapter ou rota foi promovido.

Metadados, hash e limites estao em
[`stf-informativo-live-recheck-20260901-cycle1.json`](stf-informativo-live-recheck-20260901-cycle1.json).
