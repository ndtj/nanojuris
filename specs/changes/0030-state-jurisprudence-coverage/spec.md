# 0030 — cobertura estadual de jurisprudência

Status: verified
Owner: Legal Data e Provider Engineering

## Intenção

Fechar a cobertura dos tribunais estaduais com jurisprudência textual, usando
ondas pequenas e decisão individual por fonte.

## Requisitos

- REQ-001: priorizar TJES, TJRN e TJRO textual após contratos confirmados;
  TJRJ ejuris depende de revisão de acesso.
- REQ-002: avaliar TJMG, TJRO textual e TJAP em onda separada por risco.
- REQ-003: cada provider possui identidade, parser, fixture, canonical output,
  paginação, erros, dossier e source contract próprios.
- REQ-004: famílias compartilhadas não eliminam teste por tribunal.
- REQ-005: bloqueado, partial e unavailable permanecem estados explícitos.
- REQ-006: providers silver/bronze recebem fila de maturação após as lacunas.
- REQ-007: promoção para busca unificada depende do gate 0031.
- REQ-008: cobertura estadual é medida por collection e período, não apenas por
  presença de uma fonte por TJ.
- REQ-009: primeiro e segundo graus, precedentes, informativos e documentos são
  dimensões separadas.

## Critérios de aceite

- AC-001: cada estado possui mapa de collections com runtime, candidate, lacuna
  ou bloqueio comprovado.
- AC-002: nenhum estado é contado como coberto apenas por portal conhecido.
- AC-003: onda 1 passa fixtures e contratos offline.
- AC-004: chamadas live, quando autorizadas, são bounded e registradas.
- AC-005: catálogo e documentação são gerados sem divergência.
- AC-006: percentuais estaduais exibem denominador, data e tipo documental.

## Fora de escopo

Processos, movimentos, comunicações e coleta em massa.
