# 0090 — TJRJ Banco de Sentenças

Status: `in_progress`

## Objetivo

Expor a coleção oficial de sentenças selecionadas do TJRJ como uma superfície
de primeiro grau bounded, com parser independente, links documentais observados
e estado opt-in. A implementação não declara cobertura integral do CJPG.

## Critérios de aceite

- **AC-001:** registros aceitos têm TJRJ, ramo estadual, grau/instância first,
  coleção estável e tipo sentença.
- **AC-002:** somente o PDF oficial e anotações de documento allowlisted são
  consultados; links de processo não são seguidos.
- **AC-003:** texto, frase e número são pós-filtrados de forma determinística e
  o total permanece desconhecido.
- **AC-004:** documento validado usa transporte compartilhado e MIME/hash/bytes.
- **AC-005:** erro externo, PDF inválido e documento 503 não viram vazio.
- **AC-006:** provider fica fora da federação padrão até nova evidência e revisão.

## Fora de escopo

Busca completa do TJRJ, consulta processual, enumeração de links, OCR de
CAPTCHA, login, bypass de host de documentos e claim de 27/27 CJPG.
