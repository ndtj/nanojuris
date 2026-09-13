# SDD 0093 — superfície de jurisprudência TRT15

Status: `in_progress`

## Objetivo

Adicionar o portal oficial de jurisprudência do TRT15 ao catálogo e runtime,
preservando o catálogo público e o contrato de acesso controlado sem habilitar
federação antes de existir resultado reproduzível.

## Requisitos

- **REQ-093-001** — consultar o catálogo público de órgãos e relatores.
- **REQ-093-002** — compilar os filtros declarados pelo formulário em payload
  JSON determinístico.
- **REQ-093-003** — mapear resultados autorizados para `JurisprudenceResult`
  sem inferir grau ou instância.
- **REQ-093-004** — lançar `AccessControlRequiredError` para `sucesso=3`, nunca
  retornar lista vazia.
- **REQ-093-005** — preservar hashes, status, URL e limite de bytes em trace.
- **REQ-093-006** — manter `supports_unified_search=false` até uma chamada
  pública reproduzível sem automatizar CAPTCHA.

## Critérios de aceite

- **AC-093-001** — fixture de opções é convertida em catálogo normalizado.
- **AC-093-002** — fixture autorizada é parseada com autoridade TRT15, ramo
  trabalhista e grau desconhecido.
- **AC-093-003** — CAPTCHA, 429, 5xx, schema inválido e timeout são estados
  explícitos.
- **AC-093-004** — catálogo, contrato, provider, fixture e testes são
  registrados nos inventários gerados.
