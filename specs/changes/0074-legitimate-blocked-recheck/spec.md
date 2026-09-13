# Revalidação legítima de superfícies anteriormente bloqueadas

Status: `verified`

## Objetivo

Revalidar superfícies e-SAJ que haviam sido classificadas como bloqueadas e
registrar, por chamadas públicas bounded, quando o fluxo normal de sessão volta
a entregar jurisprudência textual de segundo grau.

## Escopo

- incluir TJCE/CJSG, TJPE/Jurisprudência e TJSP/CJSG no smoke compartilhado;
- preservar classificação explícita para TJAP (Cloudflare/Turnstile) e TJMA
  (CAPTCHA server-side);
- não executar CAPTCHA, WAF, login, proxy evasivo ou qualquer bypass.

## Critérios de aceitação

- AC-001: cada fonte revalidada registra HTTP, quantidade, total e trace sem
  persistir corpo ou credenciais;
- AC-002: resultado textual de segundo grau nunca é convertido em vazio;
- AC-003: desafio de acesso continua classificado como `access_blocked`;
- AC-004: o smoke permanece bounded e usa o transporte do provider.
