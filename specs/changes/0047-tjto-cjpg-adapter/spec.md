# 0047 - adapter TJTO CJPG (primeiro grau)

Status: `proposed`  
Owner: Provider Engineering, Legal Data, Security e QA

## Intencao

Avaliar uma futura integracao da colecao CJPG do TJTO mantendo-a separada da
jurisprudencia CJSG e da consulta processual.

## Requisitos

- REQ-001: confirmar uma rota publica reproduzivel para `tip_criterio_inst=1`.
- REQ-002: validar payload, paginacao, identificador, ementa e inteiro teor.
- REQ-003: registrar bloqueios HTTP sem contornar controles de acesso.
- REQ-004: somente implementar apos fixtures sanitizadas e contrato de saida.

## Criterios de aceite

- AC-001: chamada bounded retorna dados juridicos validos ou bloqueio claramente
  documentado.
- AC-002: parser, erros, completude e rastreabilidade sao cobertos por testes.
- AC-003: a colecao permanece fora da federacao ate revisao humana.
- AC-004: nenhuma credencial, CAPTCHA, WAF ou rate limit e contornado.

## Fora de escopo

Qualquer bypass de HTTP 403, automacao de login, coleta em massa ou promocao
automatica para provider runtime.
