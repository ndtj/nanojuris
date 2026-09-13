# SDD 0100 — TSE SJUR jurisprudência textual

Status: `verified`

## Objetivo

Adicionar um adapter independente para a rota pública de pesquisa decisória do
SJUR/TSE. O adapter deve preservar os campos textuais observados, classificar
falhas de acesso explicitamente e ficar disponível como runtime opt-in; a
federação padrão permanece desabilitada até que a paginação remota seja
comprovada.

## Requisitos

- REQ-001 — usar somente `POST /tse/sjur-pesquisa-backend/rest/public/pesquisa/simples`.
- REQ-002 — enviar a consulta como DSL JSON serializada em `termoPesquisa`.
- REQ-003 — restringir o escopo ao TSE, ramo eleitoral, coleção SJUR.
- REQ-004 — preservar ementa, decisão, identidade, classe, relatoria, datas e
  campos brutos relevantes.
- REQ-005 — distinguir vazio autoritativo, sintaxe rejeitada, bloqueio,
  rate-limit, transporte e schema inválido.
- REQ-006 — não usar CAPTCHA, token, sessão autenticada, proxy ou bypass.
- REQ-007 — não declarar paginação comprovada enquanto a fonte ignorar o
  tamanho/página solicitados.
- REQ-008 — aceitar a rota pública de PDF somente para identificadores
  observados na busca, com allowlist, MIME/magic bytes, hash e limite de
  tamanho pelo pipeline documental compartilhado.

## Critérios de aceite

- AC-001 — consulta por identificador retorna registro canônico com
  `authority=TSE`, `branch=electoral`, `collection=SJUR` e `degree=superior`.
- AC-002 — a fixture de vazio só é aceita com `mensagem=null`, total zero e
  conteúdo vazio.
- AC-003 — 401/403 e respostas antirrobô geram `AccessControlRequiredError`.
- AC-004 — JSON inválido ou schema incompatível gera
  `ParserContractChangedError`.
- AC-005 — o catálogo continua separado e o adapter é runtime opt-in, com
  `supports_unified_search=false` e fora da federação padrão.
- AC-006 — o teste live bounded registra evidência sem armazenar o corpo
  completo nem dados pessoais desnecessários.
- AC-007 — `get_document` e `get_decisions` funcionam para um resultado
  observado e rejeitam identificadores não observados.

## Fora de escopo

Busca em TREs, contorno de controle de acesso, promoção GOLD e alteração de
produção. A rota PDF oficial é escopo limitado e não implica exaustividade.
