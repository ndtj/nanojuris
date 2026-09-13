# SDD 0105 — TJMSP jurisprudência diagnostic binding

Status: `verified`  
Owner: Provider Engineering  
Data: `2026-09-10`

## Objetivo

Expor a superfície oficial de pesquisa do TJMSP para diagnóstico sem mascarar
o bloqueio de acesso observado.

## Requisitos e aceite

- **REQ-001/AC-001** — usar somente GET HTTPS bounded na entrada oficial;
- **REQ-002/AC-002** — HTTP 401/403/407/451 gera `AccessControlRequiredError`;
- **REQ-003/AC-003** — shell sem contrato gera `ParserContractChangedError`;
- **REQ-004/AC-004** — capabilities são opt-in e não federadas;
- **REQ-005/AC-005** — nenhum token, cookie, credencial ou bypass é usado.

## Fora de escopo

Resolver proteção de acesso, automatizar desafios ou afirmar cobertura do acervo.
