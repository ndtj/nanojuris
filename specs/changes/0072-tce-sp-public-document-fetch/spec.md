# SDD 0072 — TCE-SP public bulletin document fetch

Status: `verified`

## Intent

Expor o inteiro teor das páginas públicas de boletins já descobertas pelo
provider `tce_sp_jurisprudencia`, sem adivinhar URLs ou automatizar a busca
protegida por reCAPTCHA.

## Requisitos

- **REQ-001** — IDs de boletim devem resolver apenas URLs HTTPS observadas na
  busca ou no catálogo da sessão atual.
- **REQ-002** — O download deve usar o transporte compartilhado, allowlist do
  host configurado e validação de MIME, tamanho, hash e proveniência.
- **REQ-003** — HTTP 4xx/5xx, redirecionamento fora da allowlist e conteúdo
  incompatível devem produzir erro explícito.
- **REQ-004** — A busca dinâmica protegida por reCAPTCHA permanece fora do
  escopo e não pode ser contornada.

## Critérios de aceitação

- **AC-001** — Resultado de boletim permite `get_document` com texto e trace.
- **AC-002** — ID arbitrário e URL de outro host são rejeitados.
- **AC-003** — Testes offline cobrem sucesso e preservam o contrato existente.
