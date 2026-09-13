# Design - TJRN jurisprudencia textual

## Evidencia de entrada

`docs/provider-discovery/juscraper-live-smoke-20260901.json` registra uma
chamada publica limitada: `POST https://jurisprudencia.tjrn.jus.br/api/pesquisar`
com `jurisprudencia.ementa`, `page` e contexto `usuario` vazio. A resposta foi
HTTP 200 JSON, 10 registros e total declarado 329883. O corpo juridico nao foi
persistido.

## Contrato a fechar

O adapter deve receber uma `JurisprudenceQuery`, construir o payload apenas com
filtros confirmados e expor um `SearchPage` com total, pagina, documentos,
`SourceTrace` e completude. Filtros anunciados mas nao reproduzidos ficam fora
da capability ate fixture propria. A origem PJe/SAJ e o grau permanecem campos
distintos; uma resposta parcial nao e convertida em acervo integral.

## Decisoes de seguranca

Sem replay de cookies, CAPTCHA, WAF ou rotas privadas. O provider nao importa
Juscraper em runtime e nao grava resposta live. Rate limit, backoff e budgets
seguem 0028/0033.
