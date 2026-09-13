# 0048 — Matriz nacional por coleção e grau

Status: verified
Owner: Arquitetura, Engenharia de Providers, Qualidade de Dados e Segurança

## Intenção

Criar uma matriz nacional verificável que distinga explicitamente `CJPG`
(primeiro grau) de `CJSG` (segundo grau) nos Tribunais de Justiça e que
represente, sem falsa equivalência, as superfícies próprias dos demais ramos
da Justiça.

## Requisitos

- REQ-001: toda linha deve identificar autoridade, ramo, grau, coleção,
  provider, status e evidências.
- REQ-002: para cada um dos 27 TJs devem existir linhas esperadas para `CJPG`
  e `CJSG`, mesmo quando a linha for lacuna, bloqueio ou contrato pendente.
- REQ-003: `CJPG` só pode ser associado a `degree=first` e `CJSG` somente a
  `degree=second`.
- REQ-004: coleções que não usam essa nomenclatura devem manter o nome da fonte
  (`EPROC`, `PJE`, `SJUR`, `PORTAL`, `PRECEDENT`, `CATALOG` etc.) e nunca ser
  promovidas automaticamente a CJPG/CJSG.
- REQ-005: o status `implemented` exige provider runtime, contrato/documentação
  e evidência local; `queryable` deve ser falso para catálogo sem busca
  decisória.
- REQ-006: graus mistos devem ser representados como `mixed` em uma superfície
  própria e permanecer como `pending_contract` para qualquer promoção a CJPG ou
  CJSG.
- REQ-007: a matriz deve tornar visíveis unidades de primeiro grau que não são
  autoridades tribunal no catálogo (varas, zonas, auditorias e unidades
  federais), sem inventar endpoints.
- REQ-008: nenhum erro externo, CAPTCHA, WAF, login, timeout ou TLS pode ser
  convertido em `empty` ou `implemented`.
- REQ-009: a geração deve ser determinística, offline e reproduzível a partir do
  catálogo de autoridades e do registro de providers.
- REQ-010: a alteração não autoriza deploy, push ou mudança de produção.
- REQ-011: cada um dos 27 TREs deve ter uma superfície própria de segundo grau
  eleitoral, separada do TSE, do agregador e das zonas eleitorais de primeiro
  grau.

## Critérios de aceite

- AC-001: a matriz contém exatamente 27 linhas `CJPG` e 27 linhas `CJSG`, uma
  por TJ estadual.
- AC-002: a validação rejeita coleção/grau incompatíveis e chaves duplicadas.
- AC-003: a saída apresenta contagens por coleção, grau, ramo e status, além de
  uma lista de lacunas acionáveis.
- AC-004: superfícies eleitorais, militares, trabalhistas, federais e superiores
  aparecem com suas coleções e graus próprios, sem serem chamadas de CJPG/CJSG.
- AC-005: providers com cobertura mista não inflacionam a cobertura de CJPG ou
  CJSG.
- AC-006: JSON e Markdown gerados são idênticos ao resultado do gerador offline.
- AC-007: testes unitários cobrem invariantes, reconciliação e lacunas.
- AC-008: `validate_sdd.py`, Ruff, mypy, compileall e a suíte relevante passam.
- AC-009: a matriz contém exatamente 27 superfícies `TRE*` de segundo grau
  eleitoral, com status explícito e sem contá-las como busca decisória quando
  a fonte só expõe metadados.

## Fora de escopo

Implementar automaticamente todos os adapters, consultar em massa fontes
oficiais, resolver CAPTCHA/WAF/login, inferir unidades judiciais ausentes do
registro institucional, alterar contratos públicos existentes ou publicar em
produção.
