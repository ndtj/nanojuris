# 0039 — ondas de adapters derivados do Juscraper

Status: verified
Owner: Provider Engineering, Security, Legal Data e QA

## Intenção

Converter somente superfícies jurisprudenciais comprovadas do snapshot
Juscraper em ganhos concretos da NanoJuris, com pacote e decisão por collection.

## Requisitos

- REQ-001: usar o ledger 0029 e a topologia 0036 como entrada obrigatória.
- REQ-002: cada adaptação fixa upstream path/commit e registra provenance.
- REQ-003: provider novo possui source ID, source contract, dossier, capability,
  fixture própria, parser, testes negativos e canonical output.
- REQ-004: overlap só altera NanoJuris quando teste diferencial prova ganho.
- REQ-005: primeiro grau é collection separada de segundo grau e processo.
- REQ-006: detalhe TJTO é lazy e falha parcial não elimina o resultado base.
- REQ-007: TJAP/TJMG não implementam bypass; TJRJ não avança sem parecer.
- REQ-008: nenhum adapter usa pandas, browser cookies ou Juscraper em runtime.
- REQ-009: cada provider inicia opt-in e passa 0031/0034 antes de default.
- REQ-010: a API TJES possui bindings separados para segundo grau, primeiro
  grau e turma recursal, embora compartilhe superfície técnica.
- REQ-011: delta upstream é revisado por `coverage_epoch`, com fingerprint e
  sem promoção automática.

## Critérios de aceite

- AC-001: TJES segundo grau, TJRN, TJRO e detalhe TJTO possuem pacote individual.
- AC-002: 19 overlaps possuem `adopt_gain`, `no_gain`, `defer` ou `blocked`.
- AC-003: `tjes_cjpg`, `tjes_turma_recursal`, `tjsp_cjpg` e `tjto_cjpg`
  possuem decisão e package.
- AC-004: fixtures e código copiado passam licença, segurança e equivalência.
- AC-005: nenhum controle de acesso é contornado.
- AC-006: docs, catálogo, interfaces e changelog permanecem sincronizados.
- AC-007: manifesto liga todas as superfícies a pacote, hardening ou bloqueio.

## Fora de escopo

Métodos processuais, agregadores autenticados e publicação em produção.
