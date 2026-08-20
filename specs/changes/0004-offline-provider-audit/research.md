# Pesquisa local

Status: `accepted`

## Escopo

Esta mudança audita o catálogo de providers e usa a camada de discovery somente
sobre arquivos versionados no repositório. Nenhuma requisição HTTP, execução de
navegador ou consulta externa faz parte da rodada.

## Evidências encontradas

- O catálogo contém 54 entradas: 44 runtime, 9 candidates mapeados e 1 família.
- Os 9 candidates possuem dossiers canônicos e cópias de contratos legados,
  mas não possuem módulo em `src/nanojuris/providers`.
- Os 9 candidates não têm fixture local referenciada nos dossiers.
- `eproc_jurisprudencia_federal` tem módulo de família, teste dedicado e três
  fixtures locais: TNU, TRF2 e TRF6.
- A extração local consegue identificar rotas e sugerir seletores nos HTMLs
  eproc, mas isso não constitui promoção de provider.

## Decisão

O relatório deve separar claramente “sem evidência offline” de “resultado vazio”
e impedir promoção automática de candidates.
