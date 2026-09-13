# 0052 - Fixture dedicada TJCE/CJSG

Status: verified
Owner: Data Quality, Provider Engineering e QA

## Intencao

Eliminar a dependencia semantica de uma fixture TJSP no teste do provider
TJCE/CJSG. A fixture dedicada deve representar o contrato HTML compartilhado
sem sugerir que registros de outro tribunal pertencam ao TJCE.

## Requisitos

- REQ-001: o teste TJCE deve carregar somente fixture identificada como TJCE;
- REQ-002: a fixture deve ser sanitizada, pequena e sem dado pessoal real;
- REQ-003: preservar os mesmos campos canônicos, paginação e links de documento
  exigidos pelo parser compartilhado;
- REQ-004: não copiar resposta live nem afirmar que a fonte está disponível;
- REQ-005: registrar o limite de que o contrato HTML compartilhado ainda exige
  confirmação live do TJCE.

## Critérios de aceite

- AC-001: testes TJCE passam usando `tests/fixtures/tjce_cjsg_result.html`;
- AC-002: a auditoria não lista `tjsp_cjsg_result.html` como evidência TJCE;
- AC-003: nenhum provider, rota ou status de acesso é promovido por esta troca;
- AC-004: SDD, Ruff, tipos e suíte passam.

## Fora de escopo

Nova chamada ao TJCE, alteração de payload, promoção de cobertura live e
redistribuição de conteúdo de tribunal.
