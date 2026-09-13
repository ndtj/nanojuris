# Rechecagem live de paridade Juscraper — 2026-09-01

Consulta pública limitada, sem credenciais, sem bypass e sem persistência de
corpos/cookies/tokens. A evidência completa está no JSON adjacente.

| Provider/transporte | Resultado | Evidência |
|---|---|---|
| TJCE/CJSG | `blocked_access` | HTTP 200 com formulário, reCAPTCHA, uuidCaptcha, rota de controle e login |
| TJPE REST | `blocked_transport` | certificado TLS inválido no ambiente; `verify_ssl=True` |
| TJPE JSF `auto` | `empty_explicit` | HTTP 200 em `POST /consulta.xhtml`, marcador explícito de zero |
| TJTO `consulta.php` | `success` | HTTP 200, 1 registro real observado, total remoto 147796 |
| TJSP/CJSG | `blocked_access` | HTTP 200 com os mesmos sinais de controle eSAJ |

O resultado não autoriza promoção automática: controles externos e o TLS do
ambiente continuam bloqueios explícitos. Produção não foi alterada.
