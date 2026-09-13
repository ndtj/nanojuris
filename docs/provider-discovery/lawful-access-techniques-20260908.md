# Técnicas legítimas de acesso a fontes públicas

A versão normativa está em
[`specs/changes/0098-national-jurisprudence-gold-coverage/lawful-access-playbook.md`](../../specs/changes/0098-national-jurisprudence-gold-coverage/lawful-access-playbook.md).

Resumo: usar APIs, exportações, RSS/sitemap/dataset, portais oficiais
equivalentes, navegador padrão, redirects allowlistados, paginação publicada,
ETag/Last-Modified, Retry-After, retry transitório e pedidos formais de
allowlist/fixture. Não usar solver de CAPTCHA, evasão de WAF/Turnstile, stealth,
rotação de IP, replay de token/cookie, fuzzing privado, downgrade de TLS ou
repetição após bloqueio.

Se a página mostrar um desafio, classificar `challenge_passive` somente quando a
jornada pública normal continua sem token especial. Se o desafio for exigido,
encerrar em `access_blocked` e procurar uma alternativa oficial.

