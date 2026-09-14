# 0114 — Matriz canônica de cobertura

Status: `in_progress`
Owner: Coverage Steward
Reviewer: Product/Legal Domain Owner
Risk: L3

## Intenção

Transformar a cobertura institucional e operacional do NanoJuris em uma fonte
tipada única, legível por pessoas e máquinas, da qual README, catálogo compacto,
fila de trabalho e documentação detalhada sejam projeções determinísticas.

## Requisitos

- REQ-001: representar todas as autoridades judiciais do registro nacional.
- REQ-002: vincular todo provider runtime a ao menos uma superfície explícita.
- REQ-003: separar implementação, verificação live e promoção federada.
- REQ-004: preservar filtros, paginação, inteiro teor, evidências e falhas por provider.
- REQ-005: impedir que conteúdo contextual quite cobertura jurisprudencial primária.
- REQ-006: gerar resumo por família imediatamente após a apresentação do README.
- REQ-007: preservar integralmente os baselines `9cd773b` e `084de4e`.

## Critérios de aceite

- AC-001: os 80 providers runtime possuem binding na matriz.
- AC-002: as 94 autoridades judiciais resolvem por ID ou alias canônico.
- AC-003: schemas, matriz, README e projeções passam no modo `--check`.
- AC-004: os 27 TREs aparecem individualmente e mantêm o provider-família.
- AC-005: bloqueio, indisponibilidade e vazio permanecem estados distintos.
- AC-006: filtros e inteiro teor são derivados do contrato real do provider.
- AC-007: o SDD v2 rejeita IDs duplicados e rastreabilidade incompleta.

## Fora de escopo

Publicação PyPI, push, tag remota, deploy e promoção de provider sem evidência.
