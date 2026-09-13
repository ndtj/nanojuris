# 0038 — semântica da busca federada

Status: verified
Owner: Search Architecture, Legal Data e QA

## Intenção

Fazer a busca unificada representar honestamente diferenças de campos,
operadores, filtros, ranking, paginação e falhas entre as fontes.

## Requisitos

- REQ-001: cada provider declara campos pesquisados e semântica de texto.
- REQ-002: o planner classifica filtros como native, translated,
  local_postfilter, unsupported ou unverified.
- REQ-003: scores nativos não são comparados entre fontes por padrão.
- REQ-004: ordenação global usa chave comparável, estável e desempate por ID.
- REQ-005: paginação global registra janela por fonte, páginas consultadas,
  truncamento e completeness.
- REQ-006: falha, timeout e bloqueio de uma fonte aparecem no envelope.
- REQ-007: deduplicação usa 0037 e não altera silenciosamente o total bruto.
- REQ-008: query plan e transformações são inspecionáveis.
- REQ-009: fonte sem suporte não recebe filtro inventado.
- REQ-010: resultados são reproduzíveis sob o mesmo manifest e fixtures.

## Critérios de aceite

- AC-001: matriz de semântica cobre todos os providers unificados.
- AC-002: testes provam que score heterogêneo não gera ranking enganoso.
- AC-003: deep pagination e falha parcial possuem resultados determinísticos.
- AC-004: query plan aparece em trace sem segredo ou PII.
- AC-005: API legada mantém compatibilidade ou depreciação documentada.
- AC-006: total federado nunca é anunciado como total nacional sem prova.

## Fora de escopo

Relevância jurídica por IA, recomendação de tese ou ranking de mérito.
