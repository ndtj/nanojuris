# Playbook de acesso público legítimo

Este documento define o máximo permitido para uma coleta de baixa frequência.
Ele não é autorização jurídica e não transforma uma fonte bloqueada em fonte
disponível.

## Permitido

1. Abrir a página pública oficial e seguir os links visíveis.
2. Usar uma sessão efêmera criada pelo próprio executor.
3. Aceitar apenas cookies e CSRF emitidos naquela sessão normal.
4. Usar navegador Chromium padrão, sem stealth, spoofing ou fingerprint falso.
5. Reproduzir somente XHR/fetch/GraphQL/BFF observados no fluxo público.
6. Seguir redirects para host oficial allowlisted e validar HTTPS/certificado.
7. Tentar HTTP/1.1 como compatibilidade, mantendo TLS e validação de certificado.
8. Repetir apenas falhas transitórias documentadas, com backoff, jitter,
   limite de frequência, timeout e teto de bytes.
9. Usar API, export, feed, catálogo, ementário ou download publicado pela
   própria autoridade.
10. Seguir documento devolvido pela fonte, validando host, MIME, magic bytes,
    tamanho, hash e conteúdo.
11. Quando uma página pública exibir CAPTCHA mas permitir continuar sem token e
    entregar dados, registrar `challenge_incidental`, sem automatizar o desafio.
12. Pedir autorização institucional ou abrir chamado oficial quando a rota
    pública legítima estiver indisponível.

## Permitido apenas com revisão humana

- retenção de inteiro teor além do cache efêmero;
- uso operacional de coleções curadas ou boletins;
- credenciais institucionais fornecidas formalmente pela autoridade;
- OCR de documento público quando necessário e permitido;
- proxies corporativos por requisito de rede, sem rotação evasiva.

## Proibido

- solver, OCR, áudio, visão ou serviço externo para resolver CAPTCHA;
- extrair, forjar ou reutilizar tokens/challenges;
- importar cookies, localStorage ou sessão de outra pessoa;
- stealth, fingerprint spoofing ou alteração artificial de User-Agent para fugir
  de controle;
- rotação de proxy/IP/ASN/User-Agent, distribuição ou concorrência para evitar
  rate limit;
- ignorar certificado, downgrade TLS ou aceitar endpoint privado;
- fuzzing, enumeração agressiva, exploração de falhas, bypass de WAF;
- acessar áreas autenticadas, sigilosas ou seladas sem autorização;
- insistir repetidamente depois de bloqueio estável.

## Protocolo de bloqueio

1. interromper a rota;
2. salvar apenas evidência redigida: URL, método, status, timestamp, tamanho,
   fingerprint e classificação;
3. marcar `access_blocked`, `challenge_enforced`, `rate_limited`, `timeout`,
   `tls_error` ou `schema_invalid`;
4. avaliar uma alternativa oficial distinta, no máximo uma vez por lote;
5. registrar ação humana necessária e avançar para o próximo provider.

Nunca converter bloqueio, timeout ou resposta inesperada em `zero_results`.
