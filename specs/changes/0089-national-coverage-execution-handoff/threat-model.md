# Threat model — coleta pública e busca live

## Ativos

- disponibilidade e reputação das fontes oficiais;
- integridade de decisões, documentos, hashes e traces;
- dados pessoais presentes em decisões públicas;
- credenciais e sessões efêmeras;
- estabilidade e custo da plataforma web.

## Ameaças e controles

| Ameaça | Controle obrigatório |
| --- | --- |
| CAPTCHA/WAF/Turnstile contornado | parar e classificar `challenge_enforced`; nunca solver/OCR/token replay |
| sobrecarga ou rate limit | orçamento por fonte, backoff, jitter, circuit breaker e baixa frequência |
| SSRF via link de documento | allowlist de host, redirect limitado, bloqueio de IP privado |
| PDF malformado/bomba de descompressão | limite de bytes/páginas, MIME + magic bytes, parser isolado |
| resposta 403/429 interpretada como vazio | estado explícito e trace redigido |
| vazamento de PII em logs/fixtures | redaction, minimização, HMAC de consulta e fixtures sanitizadas |
| drift de schema | fingerprint, fixture de drift, alerta e rollback do parser |
| cópia indevida de código Juscraper | usar contrato como referência, verificar licença e implementar independente |
| custo excessivo na web | 8–12 fontes, uma chamada normal/provider, deadline, cache efêmero |

## Limite de segurança

“Zona de sombra” não é um estado operacional aceito. Qualquer técnica que
dependa de exploração, evasão, rotação para ocultar automação, credencial não
autorizada ou acesso selado exige revisão jurídica e fica fora do executor.
