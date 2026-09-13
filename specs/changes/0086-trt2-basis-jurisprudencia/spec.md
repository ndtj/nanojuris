# SDD 0086 — TRT2 BASIS: jurisprudência curada de segundo grau

Status: `in_progress`
Owner: Provider Engineering, Data Quality e Web Search
Data: `2026-09-07`

## Problema

O endpoint público de pesquisa PJe do TRT2 apresenta desafio na rota de
documentos. Isso não deve apagar a fonte oficial de boletins que permanece
pública no repositório BASIS.

## Escopo

Implementar provider independente para a coleção DSpace oficial de “Informativos
e Boletins de Jurisprudência”, com contrato explícito de segundo grau, filtro
conservador por título, paginação bounded, link para PDF e envelope canônico.

## Critérios de aceitação

**AC-001:** Somente itens de boletim de jurisprudência TRT2 são aceitos.

**AC-002:** Todo item tem `authority=TRT2`, `branch=labor`, `degree=second`,
   `instance=second` e coleção curada.

**AC-003:** HTTP 403/429, timeout, TLS, schema inválido e MIME/PDF inválido permanecem
   estados diagnósticos distintos de vazio.

**AC-004:** Filtros não comprovados são rejeitados, não ignorados silenciosamente.

**AC-005:** Busca e documento respeitam HTTPS, allowlist, limites de bytes e transporte
   compartilhado.

**AC-006:** Fixture e chamada live bounded são reproduzíveis; a promoção fica
pendente enquanto a chamada atual não retornar registro parseado.
