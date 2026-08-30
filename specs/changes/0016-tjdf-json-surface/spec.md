# TJDFT JSON surface

Status: `verified`

## Requirements

- **REQ-001**: o provider deve expor a rota JSON sem remover o fluxo HTML.
- **REQ-002**: a conversão de paginação deve preservar a convenção pública do
  NanoJuris.
- **REQ-003**: respostas sem `hits`/`registros` ou sem identidade devem gerar
  erro explícito de contrato.
- **REQ-004**: datas, texto integral e campos desconhecidos devem ser tratados
  sem perda silenciosa de informação.
- **REQ-005**: o catálogo/capability deve declarar rota, formatos e limitação
  opt-in.

## Acceptance criteria

- **AC-001**: fixture de resultados mapeia campos canônicos e preserva `raw`.
- **AC-002**: fixture vazia resulta em página completa sem falso erro.
- **AC-003**: schema alterado é rejeitado deterministicamente.
- **AC-004**: testes existentes do fluxo HTML continuam passando.
- **AC-005**: SDD, lint e suíte local passam sem rede.

## Out of scope

Não inclui promoção automática para produção, coleta em escala, rota de
detalhe não documentada, bypass de controles ou criação de provider duplicado.
