# Tarefas — onda federal TRF1/TRF2/TRF4

- [x] **T001 [L]** Ler AGENTS, constituição, SDD 0098 e os dossiês atuais dos
  providers `cjf_jurisprudencia`, `trf2_eproc_jurisprudencia` e
  `trf4_eproc_jurisprudencia`.
- [x] **T002 [E]** Descobrir no portal oficial do TRF1 uma rota pública textual
  de segundo grau ou registrar bloqueio do CJF/TRF1.
- [x] **T003 [E]** Descobrir no portal oficial do TRF2 uma rota pública textual
  de segundo grau ou registrar a razão da rota eproc não ser suficiente.
- [x] **T004 [E]** Descobrir no portal oficial do TRF4 uma rota pública textual
  de segundo grau ou registrar a razão da rota eproc não ser suficiente.
- [x] **T005 [E]** Executar uma consulta bounded por fonte, classificando HTTP,
  conteúdo, grau, total, paginação e filtros.
- [x] **T006 [E]** Observar detalhe/documento público somente a partir de um
  identificador retornado pela mesma consulta.
- [x] **T007 [L]** Criar evidência JSON sanitizada e fixture mínima para cada
  `route_validated` ou evidência de `blocked_external`/`not_jurisprudence`.
- [x] **T008 [L]** Comparar rotas e semântica com os providers atuais e o
  inventário Juscraper sem copiar código.
- [x] **T009 [L]** Atualizar a matriz nacional e abrir workpack individual para
  cada fonte validada; não alterar rollout padrão.
- [x] **T010 [L]** Se houver contrato válido, implementar adapter independente
  apenas no lote seguinte, com transporte compartilhado e testes focados.
- [x] **T011 [L]** Executar `validate_sdd`, testes focados, Ruff, mypy e
  compileall desta meta.
- [ ] **T012 [H]** Registrar decisão humana somente se a fonte exigir licença,
  allowlist, retenção ou promoção operacional.

## Decisões fixadas em 2026-09-09

As sondas usam no máximo três páginas, intervalo de 2 segundos por provider e
nenhum paralelismo no mesmo host. Bloqueios externos continuam explícitos e
T012 não é simulado pelo executor. Ver
`docs/coverage/decision-record-20260909.json`.

## Dependências

`T001 → T002–T004 → T005–T006 → T007–T009 → T010–T011`; T012 permanece humano.
