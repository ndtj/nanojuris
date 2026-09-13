# SDD 0075 — TJAP Banco de Sentenças (CJPG)

Status: `in_progress`

## Objetivo

Adicionar uma superfície pública e independente para decisões e sentenças de
primeiro grau do TJAP, usando o Banco de Sentenças oficial (`bancosentencas`)
com o protocolo Livewire público observado. Essa superfície complementa, mas
não substitui, o Tucujuris de segundo grau, que continua explicitamente
bloqueado por Turnstile/WAF.

## Requisitos

- REQ-001: consultar somente `https://bancosentencas.tjap.jus.br/` e seu
  endpoint Livewire público, sem credenciais, cookies de desafio, CAPTCHA ou
  técnicas de evasão.
- REQ-002: normalizar apenas registros que tenham unidade de primeiro grau
  (vara, juizado, comarca ou ofício) e marcar `degree=first`, `instance=first`,
  `branch=state`, `authority=TJAP` e `collection=CJPG`.
- REQ-003: preservar processo, classe, assunto, órgão, magistrado, data de
  juntada, tipo do ato, texto público, URL oficial do leitor e `SourceTrace`.
- REQ-004: diferenciar total conhecido de total aproximado/desconhecido e
  nunca tratar falha de transporte ou schema inválido como vazio.
- REQ-005: suportar busca bounded, paginação Livewire e documento público do
  leitor somente no host oficial.

## Fora de escopo

Consulta processual, movimentações, documentos sigilosos, tentativa de obter
texto oculto, bypass de Turnstile/WAF e promoção da superfície TJAP CJSG.

## Critérios de aceite

- AC-001: busca pública com termo retorna registros de primeiro grau ou vazio
  autoritativo quando a fonte o comprovar.
- AC-002: parser rejeita cartões sem unidade de primeiro grau e não os promove
  para CJPG por inferência do termo.
- AC-003: HTTP 401/403/429, timeout e schema drift resultam em erro explícito.
- AC-004: segundo pedido Livewire usa o snapshot devolvido pela fonte e não
  persiste tokens ou corpos de resposta.
- AC-005: `get_document` aceita somente IDs/URLs observados no leitor oficial.
