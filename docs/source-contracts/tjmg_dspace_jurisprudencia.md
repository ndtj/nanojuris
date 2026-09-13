# TJMG Biblioteca Digital — CJSG

## Identity

A fonte oficial é a [Biblioteca Digital do TJMG](https://bd.tjmg.jus.br/handle/tjmg/7826).
O adapter consulta a API DSpace pública nas coleções cível, criminal e órgão
especial, que contêm registros individuais de jurisprudência de segundo grau.

## Dados

Cada item público representa uma ementa/acórdão de órgão colegiado estadual de
segundo grau. Metadados não reconhecidos são preservados em `raw`.

## Rotas

- `GET /server/api/discover/search/objects` com `query`, `scope`, `size`, `page` e
  ordenação por `dc.date.issued`.
- `GET /server/api/core/items/{uuid}/bundles` e bitstream ORIGINAL para o PDF.

Os registros são normalizados como `degree=second`, `instance=second`,
`branch=state` e coleção `CJSG_CIVEL`, `CJSG_CRIMINAL` ou
`CJSG_ORGAO_ESPECIAL`. O documento é obtido sob demanda e passa pelo pipeline
canônico, com limite de 20 MB.

## Fixtures

Fixtures sanitizadas: `tests/fixtures/tjmg_dspace_search.json`,
`tests/fixtures/tjmg_dspace_empty.json` e
`tests/fixtures/tjmg_dspace_schema_drift.json`.

## MCP

O provider expõe contrato e busca unificada pelas interfaces padrão, mantendo
a limitação de total mesclado e o documento lazy.

## Próximos passos

Monitorar periodicamente o schema DSpace e a disponibilidade dos bitstreams,
sem promover o formulário legado protegido por CAPTCHA.

## Estados e limitações

Timeout, TLS, bloqueio HTTP, rate limit, schema inválido e ausência de bitstream
são erros explícitos. O formulário legado do TJMG continua protegido por CAPTCHA
e não é contornado. A Biblioteca Digital é uma superfície pública própria; sua
integração não declara que todo o acervo do formulário legado esteja indexado.

Fixture e testes: `tests/fixtures/tjmg_dspace_search.json` e
`tests/test_tjmg_dspace_jurisprudencia.py`. Evidência live:
`docs/provider-discovery/tjmg-dspace-jurisprudencia-live-20260906.json`.
