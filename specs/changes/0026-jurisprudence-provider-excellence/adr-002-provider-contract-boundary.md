# ADR-002 — contrato comum limitado a semântica comprovável

Status: proposed
Data: 2026-09-01

## Decisão

O contrato comum representa capacidades e resultados que podem ser provados.
Filtros ou totais inexistentes em uma fonte não serão simulados silenciosamente.
Pós-filtro local só é declarado quando a janela coletada e sua incompletude são
visíveis ao consumidor.

## Consequência

A busca federada pode apresentar capacidades diferentes por fonte, mas não
produzirá a falsa impressão de equivalência nacional.
