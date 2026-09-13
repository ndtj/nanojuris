# Política de acesso público legítimo

## Permitido

- HTTP normal com TLS verificado e User-Agent identificável;
- sessão iniciada por GET no portal oficial;
- cookies e CSRF emitidos pelo próprio portal, usados somente na sessão corrente;
- redirects oficiais com allowlist de host;
- execução de JavaScript público em navegador padrão;
- XHR/fetch/GraphQL/BFF observados no fluxo público;
- APIs, exports e downloads públicos oficiais;
- HTTP/1.1 como fallback de compatibilidade sem reduzir segurança;
- retry transitório bounded, backoff, cache e rate limit conservador;
- consulta de detalhe/documento por link devolvido oficialmente;
- análise estática de bundles públicos para rotas, nomes e enums.

## Permitido somente no discovery

- navegação manual de uma página pública;
- validação humana de que um fluxo normal entrega resultado;
- inspeção de rede redigida da própria sessão;
- confirmação de que um CAPTCHA é apenas decorativo.

Token ou cookie de discovery não pode ser persistido, exportado ou reutilizado no runtime.

## Proibido

- solver, OCR ou terceirização de CAPTCHA;
- fabricar, interceptar, extrair ou reaproveitar token de CAPTCHA/Turnstile/WAF;
- cookies importados de sessão humana;
- stealth, spoofing de fingerprint ou automação disfarçada;
- rotação de proxy, IP, ASN, localização ou User-Agent para evitar bloqueio;
- distribuição de chamadas para contornar rate limit;
- TLS desativado, certificado aceito indiscriminadamente ou cipher downgrade;
- credenciais, endpoints privados, secrets em bundles ou exploração de falha;
- enumeração agressiva de rotas e fuzzing de portal;
- consulta a sigilo, segredo de justiça ou área autenticada.

## CAPTCHA

Script/widget presente não é bloqueio por si só. Classificar como
`challenge_enforced` somente quando a submissão normal sem token não entregar
resposta jurisprudencial válida ou quando o servidor exigir ação humana/token.

