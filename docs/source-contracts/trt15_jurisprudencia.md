# TRT15 Jurisprudência

Provider oficial do portal público de jurisprudência do Tribunal Regional do
Trabalho da 15ª Região.

## Estado atual

- catálogo público de órgãos julgadores e relatores: disponível;
- contrato de POST de pesquisa: identificado no bundle público;
- pesquisa live: `sucesso=3`, resposta CAPTCHA ausente/expirada;
- grau/instância: não declarado pelo resultado observado;
- federação: desabilitada;
- evidência: `docs/provider-discovery/trt15-jurisprudencia-live-20260908.json`.

O provider não tenta solver, OCR, replay ou bypass. A rota permanece útil para
diagnóstico e para futura integração caso o TRT15 ofereça API, export ou fluxo
autorizado que retorne resultados sem automatizar o desafio.

## Rotas observadas

O catalogo bounded foi revalidado em 2026-09-11: HTTP 200, 44 orgaos e 242
relatores. A evidencia sanitizada esta em
`docs/provider-discovery/trt15-jurisprudencia-options-live-20260911.json`.

## Fluxo autorizado

`search_authorized` aceita somente um `captcha_response` obtido pelo usuario
na interface oficial. O token e enviado uma unica vez, nao e criado, resolvido,
armazenado, atualizado ou reproduzido pelo provider; os traces removem os
campos do desafio e o POST permanece fora do cache. Esse caminho nao promove a
fonte automaticamente: a federacao continua desabilitada ate que grau,
instancia, paginacao e qualidade live sejam comprovados.

## Identidade

- autoridade: `TRT15`;
- ramo: trabalhista;
- coleção observada: `JURISPRUDENCIA`;
- grau e instância: desconhecidos até que um resultado autorizado os declare;
- fonte oficial: `https://jurisprudencia.trt15.jus.br`;
- escopo: catálogo e busca decisória do Tribunal Regional do Trabalho da 15ª Região.

## Dados

O contrato mapeia id, número CNJ, classe, órgão julgador, relator, ementa,
datas, link oficial, facetas e o detalhe retornado por `visualizarDocumento`.
Campos ausentes permanecem ausentes; não se infere grau, instância, tipo
documental ou inteiro teor a partir do nome da rota.

## Estados

`sucesso=1` com documentos é `success_with_results`; `sucesso=1` e total zero
é `authoritative_empty`; `sucesso=3`, HTTP 403 ou desafio são
`access_blocked`; 429 é `rate_limited`; timeout/TLS é `transport_error`;
resposta incompatível é `schema_invalid`. Nenhum desses estados é convertido
em lista vazia.

## MCP

O provider pode ser exposto para diagnóstico e catálogo pelo MCP, mas
`supports_unified_search=false` e a federação permanece desabilitada enquanto
não existir resposta de pesquisa pública reproduzível sem desafio.

## Proximos passos

1. Solicitar ao TRT15 API, export ou fluxo autorizado para pesquisa sem
   automatizar CAPTCHA.
2. Revalidar uma página pequena, segunda página, detalhe e datas somente após
   a fonte fornecer o fluxo permitido.
3. Atualizar o contrato de grau/instância e promover apenas após os oito gates.

## Fixtures

Respostas sanitizadas e versionadas do contrato:

- `tests/fixtures/trt15_jurisprudencia_options.json` — catálogo público;
- `tests/fixtures/trt15_jurisprudencia_success.json` — pesquisa autorizada;
- `tests/fixtures/trt15_jurisprudencia_page2.json` — segunda página;
- `tests/fixtures/trt15_jurisprudencia_empty.json` — vazio autoritativo;
- `tests/fixtures/trt15_jurisprudencia_captcha.json` — controle de acesso;
- `tests/fixtures/trt15_jurisprudencia_schema_drift.json` — contrato alterado.

O teste exercitado é `tests/test_trt15_jurisprudencia.py`. As respostas de
sucesso são fixtures de contrato; a chamada live atual continua em `sucesso=3`
e não autoriza a federação.

- `GET /backend/listarOpcoes` — órgãos e relatores;
- `POST /backend/pesquisar` — texto, palavras, frase, exclusões, classe,
  órgão, relator, datas, página, ordenação e tipo de busca;
- `POST /backend/irParaPagina` — paginação;
- `POST /backend/filtrarFacet` — facetas;
- `POST /backend/visualizarDocumento` — detalhe.

Filtros de grau/instância não são inferidos. Resultados só podem ser promovidos
quando trouxerem identidade canônica e texto verificável.
