# Threat model

| Ameaça | Controle |
| --- | --- |
| pressão excessiva no tribunal | orçamento, atraso, cache e circuit breaker |
| falso vazio | estados de acesso e parser sem fallback silencioso |
| SSRF por documento | allowlist, redirect revalidado e limite de bytes |
| PDF/ZIP malicioso | MIME, magic bytes, hash, compressão e quarentena |
| token/cookie vazado | redaction, TTL, nenhuma persistência de sessão |
| bypass acidental | denylist de solver, stealth, proxy evasivo e TLS relaxado |
| dados pessoais excessivos | escopo jurisprudencial, minimização e fixtures sanitizadas |
| drift de portal | fingerprint, TTL e reabertura de gates |
| abstração de família incorreta | overlay por tribunal e golden fixture próprio |
| OCR abusivo | opt-in, timeout, limite de páginas e sandbox |

403, 429, WAF, CAPTCHA obrigatório, login, TLS inválido e schema inesperado
interrompem a superfície e geram diagnóstico. Não há retry em escala nem
promoção por evidência indireta.

