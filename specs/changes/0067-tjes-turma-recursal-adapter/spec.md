# 0067 - adapter TJES Turma Recursal

Status: verified
Owner: Provider Engineering, Data Quality, Legal Data e QA

## Intencao

Implementar a superficie publica `turma_recursal_legado` do TJES como uma
collection independente. A mudanca nao conta a fonte como CJPG ou CJSG e nao
habilita federacao padrao sem os gates de reuso e release.

## Requisitos

- REQ-001: usar somente a rota oficial `GET /consulta-jurisprudencia/api/search`
  com `core=turma_recursal_legado`.
- REQ-002: mapear identificador, numero, classe, relator, orgao, data de
  julgamento e texto inline preservando o payload em `raw`.
- REQ-003: registrar `SourceTrace` e completude a partir de total, pagina e
  tamanho remoto.
- REQ-004: distinguir vazio, bloqueio, falha de transporte, schema drift e
  resposta invalida.
- REQ-005: manter a identidade semantica `TURMA_RECURSAL` separada de CJPG,
  CJSG e consulta processual.
- REQ-006: nenhum cookie, CAPTCHA, WAF bypass, credencial ou coleta em escala.

## Criterios de aceite

- AC-001: chamada live bounded reproduz HTTP 200 com documentos textuais e total.
- AC-002: fixtures sanitizadas cobrem sucesso, vazio e mudanca de schema.
- AC-003: parser gera `JurisprudenceResult` e `CanonicalDecision` com identidade
  de Turma Recursal e campos desconhecidos preservados.
- AC-004: testes cobrem parametros, paginacao, trace e outcomes HTTP 4xx/429/5xx.
- AC-005: provider e registrado no runtime e permanece opt-in na federacao.
- AC-006: nenhuma publicacao, push, deploy ou alteracao de producao e realizada.

## Fora de escopo

Detalhe nao observado, ingestao em massa, OCR, consulta processual, CJPG/CJSG
e aprovacao juridica de redistribuicao.
