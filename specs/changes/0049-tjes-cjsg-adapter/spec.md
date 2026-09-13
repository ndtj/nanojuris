# 0049 — Adapter TJES/CJSG (segundo grau)

Status: verified
Owner: Engenharia de Providers e Qualidade de Dados

## Intenção

Promover a superfície pública JSON `pje2g` do TJES como provider de
jurisprudência de segundo grau, mantendo-a separada do adapter `tjes_cjpg`
(`pje1g`).

## Requisitos

- REQ-001: consultar somente `GET /api/search` com `core=pje2g`.
- REQ-002: mapear `docs`, `total`, `page` e `per_page` para o contrato
  `SearchPage`, preservando o documento original em `raw`.
- REQ-003: mapear identificador, número, ementa, acórdão, relator, órgão,
  classe, assunto e data sem inventar valores ausentes.
- REQ-004: classificar HTTP 401/403 como controle de acesso, 429 como limite,
  4xx de consulta como rejeição, 5xx/erro de transporte como indisponibilidade
  e JSON incompatível como mudança de contrato.
- REQ-005: limitar paginação a 20 itens por página e respeitar o intervalo
  global de requisições.
- REQ-006: expor `collection=second_degree;core=pje2g` e não misturar CJPG,
  `pje2g_mono`, legado ou consulta processual.
- REQ-007: fornecer fixtures sanitizadas de sucesso, vazio, erro e mudança de
  schema, além de testes de parser, query e rastreabilidade.
- REQ-008: a alteração é local e não autoriza deploy, push ou federação
  automática sem revisão de reuso.

## Critérios de aceite

- AC-001: busca com fixture válida retorna `CanonicalDecision` equivalente,
  ementa e acórdão preservados.
- AC-002: página vazia é distinguida de erro e mantém completude explícita.
- AC-003: core diferente de `pje2g`, total/página inválidos e documentos sem
  identidade são rejeitados.
- AC-004: erros HTTP e transporte preservam diagnóstico em `SourceTrace`.
- AC-005: `NanoJurisClient` lista `tjes_jurisprudencia` sem alterar o provider
  CJPG existente.
- AC-006: catálogo, dossiê, contrato legado e matriz de cobertura são
  regenerados a partir do runtime.

## Fora de escopo

Detalhe independente, download de PDF, cores `pje2g_mono`/`legado`, captura em
escala, bypass de controle de acesso e publicação em produção.
