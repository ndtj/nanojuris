# SDD 0111 — TRT4 Súmulas e precedentes

Status: `verified`  
Owner: Provider Engineering  
Data: 2026-09-10

## Objetivo

Expor a coleção pública oficial de súmulas, orientações e acórdãos vinculados
do TRT4 como fonte contextual de segundo grau, sem alegar cobertura do corpus
geral do tribunal.

## Requisitos

- **REQ-001** — consultar somente a página oficial allowlisted do TRT4;
- **REQ-002** — identificar títulos de súmula, orientação e acórdão com links;
- **REQ-003** — normalizar autoridade, ramo, grau, instância, coleção e tipo;
- **REQ-004** — aplicar texto, frase, número e exclusão localmente;
- **REQ-005** — distinguir HTML inválido, bloqueio, timeout, rate limit e schema drift;
- **REQ-006** — manter a fonte contextual/opt-in e fora da federação padrão.

## Fora de escopo

Busca geral Falcão, paginação remota, acervo integral, OCR, bypass de controles
e deploy.

## Acceptance criteria IDs

- `AC-001` — o adapter acessa apenas a rota oficial TRT4 e valida HTML;
- `AC-002` — cada registro aceito preserva `authority=TRT4`, `branch=labor`,
  `degree=second`, `instance=second`, `collection=TRT4_SUMULAS` e tipo;
- `AC-003` — filtros locais e janela de página funcionam sem converter erro ou
  schema inválido em vazio;
- `AC-004` — sonda live e documento observado preservam `SourceTrace`;
- `AC-005` — a coleção permanece contextual/opt-in e não é apresentada como
  cobertura geral TRT4.

## Aceite

Adapter, fixture, testes, evidência live e gates locais verdes; promoção padrão
desabilitada por decisão técnica.
