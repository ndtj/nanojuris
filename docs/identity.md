# Identidade jurídica canônica

Este documento descreve a projeção opcional de identidade adicionada na v1.
Ela não altera os campos históricos dos modelos nem o `canonical_key` usado por
consultas legadas.

## Regras

- `process` pode usar o número CNJ normalizado (`process:cnj:<20 dígitos>`).
- `decision` usa o identificador nativo do provider quando presente. Sem ele,
  exige autoridade, grau, tipo e data; número CNJ sozinho nunca identifica uma
  decisão.
- `precedent` usa identificador nativo ou o par tipo/número no namespace da
  fonte.
- `document`/`version` usa identificador nativo ou pai mais hash do conteúdo.
- `publication` exige identificador nativo.

Quando a evidência é insuficiente, `key` fica nulo e `unresolved_reason`
explica o motivo. A comparação retorna `same`, `distinct` ou `unknown`; não há
merge destrutivo nem inferência de identidade civil.

## Store e exportação

`SQLiteStore` grava a projeção em `legal_identity_json` e a anexa aos registros
retornados sem remover campos legados. `get_identity(kind, id)` permite ler a
projeção diretamente. JSONL, CSV e exportações de pesquisas salvas incluem os
campos de identidade para que o roundtrip preserve a linhagem.

O campo `raw` continua sendo a fonte dos valores originais. Alterações futuras
nas regras devem criar uma versão explícita e reprocessar matches, sem mudar
IDs antigos silenciosamente.
