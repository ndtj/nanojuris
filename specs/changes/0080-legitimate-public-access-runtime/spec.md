# 0080 — runtime de acesso público legítimo

Status: `proposed`

Implementar descoberta bounded por HTTP e navegador padrão, sem bypass de
CAPTCHA, WAF, login, TLS ou rate limit.

- **AC-001:** marcador passivo de CAPTCHA não gera bloqueio quando a busca normal funciona.
- **AC-002:** desafio efetivamente exigido gera `challenge_enforced`, nunca vazio.
- **AC-003:** cookies/CSRF ficam limitados à sessão corrente e não são persistidos.
- **AC-004:** redirects, TLS, 403, 429 e schema são testados explicitamente.

