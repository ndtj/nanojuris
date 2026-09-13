# Threat model — coleta pública e cobertura nacional

| Ameaça | Impacto | Controles |
| --- | --- | --- |
| Bypass acidental de CAPTCHA/WAF | legal, bloqueio de fonte, reputação | playbook, allowlist, parada em bloqueio |
| SSRF por URL de documento | acesso interno | host allowlist, redirects restritos, DNS/IP validation |
| Resposta comprimida abusiva | exaustão de memória | limites comprimido/descomprimido, streaming |
| PDF/HTML malformado | parser crash ou XSS | MIME, sandbox de extração, sanitização |
| PII em fixture/log | exposição de dados | redaction, minimização, hashes e retenção |
| Token/cookie persistido | acesso indevido | sessão efêmera, secret scanner, não registrar headers |
| Schema drift | falso vazio ou corrupção | fingerprint, schema_invalid, alerta |
| Rate limit excedido | bloqueio e indisponibilidade | baixa frequência, Retry-After, circuit breaker |
| Duplicidade/republicação | ranking e jurimetria incorretos | identidade, fingerprint, versionamento |
| Grau incorreto | cobertura falsa | validação de authority/degree/instance |
| Código de terceiro copiado | licença e manutenção | diff semântico, implementação independente |
| Falsa aprovação humana | risco operacional | gates `[H]`, assinatura/registro externo |

## Controles de dados

- TLS sempre verificado; nenhuma credencial no repositório.
- Logs não registram texto integral, e-mail, IP analítico ou tokens.
- Cache não é um corpus pesquisável e possui TTL/invalidação.
- Documentos são buscados sob demanda e respeitam retenção definida pelo owner.

