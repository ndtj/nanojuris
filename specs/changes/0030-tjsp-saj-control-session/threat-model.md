# Threat model

| Risco | Mitigacao |
| --- | --- |
| Resolver CAPTCHA | Nenhum solver ou token reCAPTCHA e usado. |
| Fabricar UUID | O valor vem exclusivamente do JSON da fonte. |
| Persistir sessao | `requests.Session` permanece efemera em memoria. |
| Tratar controle como resultado | O POST continua passando pelo diagnostico de acesso. |
| Sobrecarga da fonte | O rate limit existente do provider continua ativo. |
