# SDD 0106 — diagnóstico TRT6 Jurisprudência

Status: `verified`  
Owner: Provider Engineering  
Data: `2026-09-10`

## Objetivo

Registrar uma integração técnica segura para as duas entradas oficiais de
jurisprudência do TRT6 sem afirmar cobertura textual enquanto o acesso público
exigir desafio humano.

## Escopo

- metadados públicos do backend PJe;
- catálogo público de filtros do backend PJe, sem documentos de resultados;
- inspeção do formulário legado de Consulta de Acórdãos;
- classificação explícita de reCAPTCHA, HTTP 4xx/429 e falhas de transporte;
- nenhum token, cookie, sessão autenticada ou bypass.

## Fora de escopo

- resolução ou automação de CAPTCHA/reCAPTCHA;
- promoção à federação padrão;
- alegação de paginação, resultados, detalhe ou inteiro teor sem evidência;
- deploy, credenciais ou alteração de produção.

## Requisitos e aceite

- **REQ-001/AC-001** — `get_parameters()` retorna somente metadados públicos redigidos.
- **REQ-002/AC-002** — `get_legacy_form()` identifica campos e necessidade de reCAPTCHA.
- **REQ-003/AC-003** — busca sem token gera `AccessControlRequiredError`.
- **REQ-004/AC-004** — nenhuma falha de acesso é convertida em página vazia.
- **REQ-005/AC-005** — provider permanece `opt_in_unified_search=true` e fora do rollout padrão.
- **REQ-006/AC-006** — `get_filter_catalog()` resume agregações públicas de filtros
  sem persistir documentos e sem classificar metadados como resultados de busca.
