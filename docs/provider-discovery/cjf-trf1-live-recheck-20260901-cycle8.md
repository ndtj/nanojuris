# Rechecagem live CJF/TRF1 - 2026-09-01 (ciclo 8)

Foi feita uma rechecagem publica bounded da entrada oficial do TRF1 no CJF,
sem credenciais e sem persistir o corpo. A rota respondeu HTTP 200, mas o
HTML continha marcadores de CAPTCHA/reCAPTCHA, sem tabela de resultados.

| Tentativa | Resultado | Classificacao |
| --- | --- | --- |
| GET `/trf1/index.xhtml` com TLS padrao | HTTP 200, 16.685 bytes | `blocked_access` |

O provider continua runtime com o contrato local existente, mas esta rodada
nao prova disponibilidade de busca. Nenhum POST com ViewState foi enviado
apos o desafio e nenhum resultado foi promovido ou convertido em vazio.

Metadados, hash e limites estao em
[`cjf-trf1-live-recheck-20260901-cycle8.json`](cjf-trf1-live-recheck-20260901-cycle8.json).
