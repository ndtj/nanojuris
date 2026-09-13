# Threat model — cobertura pública e handoff

## Ativos

- integridade de decisões, documentos, hashes e traces;
- disponibilidade e reputação dos portais oficiais;
- dados pessoais contidos em decisões públicas;
- sessões efêmeras, credenciais e custos de execução;
- determinismo do ranking e confiança da plataforma.

## Ameaças e controles

| Ameaça | Controle |
| --- | --- |
| CAPTCHA/Turnstile/WAF tratado como obstáculo a evadir | parar, registrar `challenge_enforced` e procurar apenas export/API/rota oficial |
| excesso de requests ou rate limit | orçamento por fonte, backoff, jitter, circuit breaker e baixa frequência |
| SSRF por URL de documento | allowlist de host, redirects limitados, bloqueio de IP privado |
| PDF malformado ou bomba de descompressão | MIME + magic bytes, limites de bytes/páginas e parser isolado |
| 403/429/TLS interpretado como vazio | estado operacional explícito e trace redigido |
| vazamento de PII | minimização, redaction, HMAC de consulta e fixtures sanitizadas |
| schema drift | fingerprint, fixture de drift, alerta e rollback |
| cópia incompatível do Juscraper | fixar licença/commit, comparar contrato e implementar independentemente |
| custo excessivo na busca web | 8–12 fontes, uma chamada normal/provider, deadline e cache efêmero |
| pressão para “zona de sombra” | proibir solver, stealth, replay, rotação de IP, TLS downgrade e endpoint privado |

## Fronteira de acesso

Permitidos: página pública documentada, GET/POST normal sem credencial,
redirect oficial, cookie/CSRF emitido para a própria sessão efêmera, paginação
publicada, export/API oficial, sitemap/RSS, retry transitório cooperativo,
allowlist concedida pelo responsável da fonte e desafio resolvido manualmente
pelo usuário sem persistir token.

Proibidos: automação ou OCR de CAPTCHA/Turnstile, bypass de WAF, spoofing de
fingerprint, proxy/rotação para ocultar automação, replay de cookies/tokens,
desativar TLS, fuzzing de endpoints privados, contornar autenticação, exaurir
rate limit ou acessar dado restrito. “Zona de sombra” não é um estado técnico
aceito.
