# 0066 - contratos de superficie e grau para adapters estaduais

Status: `verified`
Owner: Provider/Data Engineering

## Intencao

Fechar a normalizacao aditiva das superficies estaduais prioritarias sem
confundir uma busca unificada (que pode misturar primeiro e segundo grau) com
uma prova de CJPG ou CJSG. Cada resultado deve carregar identidade de fonte,
colecao, ramo, tipo documental e grau quando a fonte o informar.

## Requisitos

- REQ-001: resultados TJRN, TJRO, TJTO e TJGO devem expor `authority`, `branch`,
  `collection` e `document_type` de forma canonica, preservando os campos
  nativos em `raw`.
- REQ-002: TJRN e TJRO devem normalizar rotulos numericos/textuais de grau e
  instancia para `first`, `second`, `recursal`, `superior` ou `unknown` sem
  inventar grau ausente.
- REQ-003: paginas dos adapters prioritarios devem declarar `total_known`,
  `access_status` e `extraction_status`; total sintetico nao pode ser tratado
  como total remoto autoritativo.
- REQ-004: colecao generica `JURISPRUDENCIA` nao pode creditar automaticamente
  uma superficie CJPG ou CJSG na matriz nacional.
- REQ-005: a alteracao deve ser aditiva e preservar compatibilidade da API v1;
  nenhum provider bloqueado deve ser promovido por este pacote.
- REQ-006: nenhuma acao de release, push, deploy ou producao faz parte deste
  pacote.

## Criterios de aceite

- AC-001: fixtures sanitizadas cobrem campos canonicos dos quatro adapters.
- AC-002: total explicito zero, total conhecido positivo e total desconhecido
  permanecem estados distinguiveis.
- AC-003: conversao para `CanonicalDecision` passa a validacao sem warnings de
  dimensao para as fixtures prioritarias.
- AC-004: dossiers canonico e legado permanecem em paridade.
- AC-005: Ruff, mypy, compileall, SDD e suite completa passam.

## Fora de escopo

Promocao legal, novas rotas sem contrato, CAPTCHA/WAF/login, OCR, alteracao de
infraestrutura, publicacao e declaracao de cobertura nacional completa.
