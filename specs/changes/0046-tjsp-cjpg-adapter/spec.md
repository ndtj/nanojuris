# 0046 - adapter TJSP CJPG (primeiro grau)

Status: verified
Owner: Provider Engineering, Legal Data, Security e QA

## Intencao

Adicionar a fonte publica de jurisprudencia de primeiro grau (CJPG) do TJSP
sem misturar sua semantica com CJSG, consulta processual ou precedentes.

## Requisitos

- REQ-001: usar somente as rotas publicas `cjpg/pesquisar.do` e
  `cjpg/trocarDePagina.do` observadas no e-SAJ.
- REQ-002: mapear numero, classe, assunto, magistrado, comarca, foro, vara,
  disponibilidade e decisao inline.
- REQ-003: preservar campos de origem e emitir `SourceTrace` com URL, status,
  tipo, bytes, tempo e hash.
- REQ-004: respeitar o limite remoto de 10 itens por pagina, timeout, SSL e
  rate limit configurados.
- REQ-005: distinguir vazio confirmado, bloqueio, HTTP, timeout e schema drift.
- REQ-006: manter `supports_unified_search=False` enquanto a colecao estiver
  em revisao juridica e de equivalencia.
- REQ-007: nao contornar CAPTCHA, WAF, login, robots, sessao ou rate limit.

## Criterios de aceite

- AC-001: chamada publica bounded reproduz HTTP 200, linhas e total.
- AC-002: fixtures sanitizadas cobrem sucesso, vazio, acesso e drift.
- AC-003: parser mapeia `JurisprudenceResult` e `CanonicalDecision` com texto.
- AC-004: testes cobrem payload, paginacao, trace e HTTP outcomes.
- AC-005: catalogo, docs e inventario identificam a fonte como opt-in e 1o grau.
- AC-006: nenhum deploy, push ou alteracao de producao e realizado.

## Fora de escopo

Coleta em massa, rota de detalhe nao observada, redistribuicao do corpus,
federacao automatica, segundo grau/CJSG e consulta processual.
