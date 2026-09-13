# ADR-003 — evidência offline como base de regressão

Status: proposed
Data: 2026-09-01

## Decisão

Fixtures minimizadas, golden outputs e testes locais são a base de regressão.
Chamadas live são canários temporais opt-in e bounded, nunca pré-requisito
automático para instalar ou testar a biblioteca.

## Consequências

- CI permanece determinística;
- fontes oficiais recebem menos tráfego;
- saúde live requer timestamp e não pode ser inferida de fixture;
- schema drift é confirmado antes de atualizar fixtures.
