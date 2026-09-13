# TJMG/EJEF - Boletim de Jurisprudencia

## Identidade

- `source_id`: `tjmg_ejef_boletim_jurisprudencia`;
- autoridade: `TJMG`;
- ramo: `state`;
- grau e instancia: `second`;
- colecao: `CJSG_EJEF_BOLETIM`;
- fonte oficial: [EJEF](https://ejef.tjmg.jus.br/boletim-de-jurisprudencia/);
- colecao DSpace: [Biblioteca Digital](https://bd.tjmg.jus.br/collections/c4bd64ae-089d-446c-966f-2ba332a0cbf5).

## Contrato

O adapter usa exclusivamente a API publica DSpace da colecao oficial do
Boletim de Jurisprudencia. A busca envia `query`, `scope`, `size`, `page` e
ordenacao por `dc.date.issued,DESC` para
`GET /server/api/discover/search/objects`. O resultado informa
`totalElements`, o que permite distinguir vazio autoritativo de total
desconhecido.

Cada item e normalizado como decisao de segundo grau. O documento original e
obtido sob demanda por `items/{uuid}/bundles`, pelo bitstream `ORIGINAL` e
pela rota publica de conteudo. O limite de documento segue o limite comum de
20 MB.

## Dados preservados

Titulo do boletim, assuntos, autor institucional, data de publicacao, handle,
UUID do item, URL do item, resumo/ementa, URL do PDF, MIME, tamanho, hashes e
`SourceTrace`. A colecao e curada e historica: nao representa o acervo
integral da busca geral do TJMG.

## Filtros e paginacao

Suportados: texto, frase exata, numero quando presente, pagina e filtros
semanticos validados de autoridade, ramo, grau, instancia e colecao. Classe,
relator, orgao, partes e intervalos temporais nao sao inferidos; permanecem
explicitamente nao suportados. A paginacao e offset, limitada a 20 itens por
chamada.

## Estados e limites

HTTP 401/403/429, TLS, timeout, schema invalido e bitstream ausente sao erros
explicitos. HTTP 200 com `totalElements=0` e `authoritative_empty`. PDFs
image-only nao recebem OCR automatico. O formulario legado do TJMG protegido
por CAPTCHA nao e utilizado nem contornado.

## Fixtures

As fixtures sanitizadas versionadas cobrem os envelopes de sucesso, vazio
autoritativo e schema invalido em `tests/fixtures/tjmg_ejef_boletim_search.json`,
`tests/fixtures/tjmg_ejef_boletim_empty.json` e
`tests/fixtures/tjmg_ejef_boletim_invalid.json`.
O cenario de documento e exercitado pelo teste de bundle/bitstream com PDF
sintetico, sem persistir o corpo obtido da fonte oficial. O envelope
compartilhado de transporte cobre falha externa e segunda pagina quando
aplicavel.

## Evidencia e testes

- evidencia live: `docs/provider-discovery/tjmg-ejef-boletim-live-20260908.json`;
- testes: `tests/test_tjmg_ejef_boletim_jurisprudencia.py`;
- implementacao: `src/nanojuris/providers/tjmg_ejef_boletim_jurisprudencia.py`.

## MCP e interfaces

O provider declara CLI, MCP, Studio e busca federada. A federacao deve exibir
que a fonte e parcial/curada, preservando `totalElements` e a explicacao de
escopo no diagnostico.

## Proximos passos

Revalidar o UUID e o schema DSpace em smoke periodico, acompanhar novos
boletins e avaliar promocao operacional conforme a politica de retencao. Nao
afirmar cobertura integral do TJMG a partir desta colecao.
