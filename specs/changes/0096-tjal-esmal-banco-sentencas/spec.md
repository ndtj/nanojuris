# Especificação — TJAL ESMAL Banco de Sentenças

## Objetivo

Disponibilizar no NanoJuris uma consulta reproduzível ao banco público de
sentenças selecionadas da ESMAL, preservando a identidade de primeiro grau,
filtros observados e os links oficiais para documentos PDF.

## Requisitos funcionais

- RF-001 — consultar `https://esmal.tjal.jus.br/indexS.php?pag=ler` por GET,
  usando `cat` e `text` conforme o contrato público observado.
- RF-002 — aceitar categorias oficiais (`A`, `C`, `P`, `E`, `V`, `T`, `D`, `J`)
  e texto/f​​rase/número como filtros remotos.
- RF-003 — extrair data, título e URL PDF oficial de cada linha de resultado.
- RF-004 — preservar `authority=TJAL`, `branch=state`, `degree=first`,
  `instance=first`, `collection=TJAL_ESMAL_CJPG` e `document_type=sentenca`.
- RF-005 — suportar janela de página pública sem declarar total autoritativo.
- RF-006 — buscar PDF observado somente no host oficial allowlisted e validar
  MIME, assinatura, tamanho e texto extraível.
- RF-007 — classificar timeout, 403, 429, TLS, schema inválido e PDF inválido
  explicitamente; nunca convertê-los em vazio.
- RF-008 — declarar `supports_unified_search=true` após os gates técnicos,
  mantendo a coleção como fonte parcial, curada e `total_known=false`; isso
  não afirma cobertura integral do CJPG.

## Fora de escopo

Consulta processual, documentos não publicados, autenticação, CAPTCHA, OCR,
varredura de diretórios, enumeração de arquivos ou qualquer bypass de controle.

## Critérios de aceitação

- AC-001 — chamada live com `cat=C,text=responsabilidade` retorna registros
  textuais e URLs PDF oficiais.
- AC-002 — termo inexistente produz zero autoritativo apenas quando a página
  declara ausência; resposta sem linhas sem declaração permanece `unconfirmed`.
- AC-003 — uma segunda página produz janela distinta quando a fonte a publica.
- AC-004 — todos os registros aceitos têm identidade CJPG explícita e trace.
- AC-005 — fixture de sucesso, vazio, bloqueio, schema inválido e PDF inválido
  cobre o parser e o fetch documental.
- AC-006 — testes, Ruff, mypy, compileall e validação SDD passam.
Status: in_progress
