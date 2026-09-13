# Rechecagem live TJSP/CJSG - 2026-09-01 (ciclo 11)

Foi feita uma chamada POST publica bounded ao fluxo contratado do TJSP/CJSG,
sem credenciais. A resposta foi classificada como `blocked_access` porque a
superficie apresentou formulário, reCAPTCHA, UUID de captcha, rota de controle
de acesso e script de login.

| Rota | Resultado | Classificacao |
| --- | --- | --- |
| `POST /resultadoCompleta.do` | `AccessControlRequiredError` | `blocked_access` |

Nenhum CAPTCHA ou login foi contornado, e nenhum corpo live foi persistido. O
provider permanece inalterado e não anuncia resultados nesta fotografia.

Metadados estao em
[`tjsp-cjsg-live-recheck-20260901-cycle11.json`](tjsp-cjsg-live-recheck-20260901-cycle11.json).
