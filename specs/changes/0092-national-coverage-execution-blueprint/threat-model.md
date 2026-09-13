# Threat model — coleta pública de jurisprudência

## Ativos

- integridade de decisões, documentos, hashes e traces;
- disponibilidade e reputação dos portais oficiais;
- dados pessoais presentes em decisões públicas;
- cookies efêmeros, custos e credenciais fora do repositório;
- confiança no diagnóstico de cobertura e ranking.

## Ameaças e controles

| Ameaça | Controle obrigatório |
| --- | --- |
| CAPTCHA/Turnstile automatizado | parar; classificar `access_blocked`; procurar API/export/allowlist |
| WAF ou rate limit | backoff cooperativo, circuit breaker e baixa frequência; nunca evasão |
| SSRF em documento | allowlist de host, redirects limitados, bloquear IP privado |
| PDF malformado/bomba | limite de bytes/páginas, MIME + magic bytes, parser isolado |
| TLS/403/429 como vazio | estado operacional explícito e trace redigido |
| PII em fixture/log | minimização, redaction, HMAC quando necessário |
| schema drift | fingerprint, fixture de drift, alerta e rollback |
| cópia incompatível do Juscraper | fixar commit/licença e implementar parser próprio |
| custo excessivo | 8–12 fontes adaptativas, deadline e cache efêmero |
| pressão por “zona de sombra” | proibidos solver, stealth, replay, spoofing, proxy evasivo e downgrade TLS |

## Limites legais/operacionais

Permitidos: página pública, API/export oficial, browser normal, cookie/CSRF da
própria sessão, paginação documentada, ETag, sitemap/RSS, retry transitório,
suporte/allowlist formal e desafio resolvido manualmente pelo usuário.

Proibidos: OCR/solver de desafio, contorno de login, replay de token, rotação
de IP para ocultar automação, fuzzing de endpoint privado, exaustão de limite,
desativação de TLS e acesso a informação restrita. “Zona de sombra” não é um
estado aceitável de implementação.
