# SDD 0101 — TJMRS jurisprudência por processo exato

Status: `verified`  
Owner: Provider Engineering  
Data: `2026-09-09`

## Objetivo

Adicionar uma superfície técnica para consultar o inteiro teor público de um
acórdão do Tribunal de Justiça Militar do Rio Grande do Sul por número CNJ
exato, sem promovê-la como corpus textual geral.

## Requisitos

- **REQ-001** — aceitar somente processo CNJ exato e página 1.
- **REQ-002** — aceitar o registro apenas quando a página comprovar acórdão,
  ementa, relator e autoridade TJMRS.
- **REQ-003** — normalizar `branch=military`, `degree=second`,
  `instance=second`, `collection=TJMRS_JURISPRUDENCIA` e
  `document_type=acordao`.
- **REQ-004** — preservar inteiro teor HTML, URL, hash, tamanho e `SourceTrace`
  no fluxo explícito de documento.
- **REQ-005** — distinguir vazio autoritativo de bloqueio, timeout, erro HTTP e
  mudança de schema.
- **REQ-006** — manter `supports_unified_search=false` e
  `opt_in_unified_search=true` enquanto não houver busca geral e paginação
  comprovadas.

## Critérios de aceite

- **AC-001** — parser de sucesso, vazio e shape inesperado coberto por fixtures.
- **AC-002** — filtros não suportados e segunda página são rejeitados.
- **AC-003** — HTTP 403 não vira lista vazia.
- **AC-004** — `get_document` retorna `CanonicalDocument` público com texto e
  bytes preservados.
- **AC-005** — chamada live bounded oficial registra duas decisões e um vazio
  explícito, sem persistir corpo bruto.
- **AC-006** — provider é runtime opt-in e não é roteado pela federação padrão.

## Fora de escopo

Busca livre, paginação de corpus, captura de CAPTCHA/WAF, login, uso de
credenciais, reconstituição de cookies, OCR e cobertura automática de TJMMG ou
TJMSP.
