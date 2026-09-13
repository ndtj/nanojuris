# SDD 0110 — TRT9 NUGEP/NUGEPNAC

Status: `verified`  
Owner: Provider Engineering  
Data: 2026-09-10

## Objetivo

Expor compilações públicas oficiais de precedentes qualificados do TRT9 como
fonte contextual de segundo grau, sem alegar que elas substituem a busca geral.

## Requisitos

- **REQ-001** — consultar somente os PDFs oficiais allowlisted do TRT9;
- **REQ-002** — extrair blocos com identificador CNJ e preservar o texto;
- **REQ-003** — normalizar autoridade, ramo, grau, instância e coleção;
- **REQ-004** — aplicar texto, frase, número e negação localmente;
- **REQ-005** — distinguir PDF inválido, bloqueio, timeout, rate limit e schema drift;
- **REQ-006** — manter a fonte contextual/opt-in e fora da federação padrão.

## Fora de escopo

Corpus geral TRT9, paginação remota, inteiro teor de votos, OCR, bypass de
controles e deploy.

## Acceptance criteria IDs

- `AC-001` — o adapter acessa somente as rotas oficiais TRT9 allowlisted e valida `%PDF`;
- `AC-002` — cada registro aceito preserva `authority=TRT9`, `branch=labor`,
  `degree=second`, `instance=second` e uma coleção NUGEP explícita;
- `AC-003` — texto, frase, número, negação e janela local são aplicados sem
  converter PDF inválido, bloqueio ou schema drift em vazio;
- `AC-004` — a sonda live reproduzível e o documento observado mantêm trace e
  permanecem contextuais/opt-in;
- `AC-005` — a fonte não é declarada como cobertura geral nem entra na federação
  padrão enquanto não houver contrato de busca geral.

## Aceite

Adapter, fixture, testes, evidência live e gates locais verdes; promoção padrão
desabilitada por decisão técnica.
