# 0065 — contrato de qualidade e completude de dados

Status: `verified`

## Intenção

Fechar os riscos P0/P1 identificados na auditoria sem promover fontes externas
sem evidência. A camada pública deve distinguir total desconhecido de total
zero, expor o estado de acesso por página e transportar filtros canônicos sem
perder compatibilidade com a API v1.

## Requisitos

- REQ-001: `SearchPage` deve representar explicitamente se o total remoto é
  conhecido e o estado de acesso/extração da página.
- REQ-002: a federação nunca deve parar por `total=0` quando o total não foi
  comprovado pelo provider.
- REQ-003: consulta, resultado canônico e armazenamento devem aceitar classe,
  órgão, grau, ramo, área, autoridade, coleção e tipo documental como campos
  aditivos e serializáveis.
- REQ-004: consultas locais devem indexar os campos canônicos novos e manter o
  JSON bruto para auditoria.
- REQ-005: bloqueio, timeout, schema inválido e conteúdo vazio devem permanecer
  estados distintos de resultado vazio.
- REQ-006: nenhuma alteração deste pacote publica, faz push ou altera produção.

## Critérios de aceite

- AC-001: providers legados continuam construindo `SearchPage` sem mudanças.
- AC-002: paginação federada só usa total remoto quando `total_known=True`.
- AC-003: filtros novos são validados, encaminhados e aparecem em
  `filters_applied`/traces quando suportados.
- AC-004: SQLite novo e banco legado recebem migração idempotente, índices e
  filtros equivalentes.
- AC-005: testes cobrem total desconhecido, vazio explícito, bloqueio, filtros,
  migração e round-trip JSON.
- AC-006: Ruff, mypy, compileall, SDD e suíte completa passam.

## Fora de escopo

Promover candidatos, contornar controles de acesso, OCR de documentos, deploy,
publicação ou afirmar cobertura nacional sem chamada reproduzível.
