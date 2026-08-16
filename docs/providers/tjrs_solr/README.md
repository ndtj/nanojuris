# TJRS - Jurisprudencia AJAX/SOLR

Status atual: `implemented` para busca JSON/SOLR; detalhe e inteiro teor ainda
nao estao promovidos.

## Identidade e escopo

- Fonte oficial: portal de jurisprudencia do Tribunal de Justica do Rio Grande
  do Sul.
- Categoria: `court_jurisprudence`.
- Familia tecnica: formulario AJAX legado com resposta SOLR-like em JSON.
- O provider cobre busca de jurisprudencia e metadados retornados pelo indice;
  nao representa consulta processual nem garante inteiro teor.

## Contrato HTTP

- Portal: `https://www.tjrs.jus.br/novo/buscas-solr/?aba=jurisprudencia`.
- Iframe: `https://www.tjrs.jus.br/buscas/jurisprudencia/`.
- Endpoint: `POST https://www.tjrs.jus.br/buscas/jurisprudencia/ajax.php`.
- Tipo observado: JSON com header legado `text/html; charset=iso-8859-1`.

Payload minimo reproduzido:

```text
action=consultas_solr_ajax
metodo=buscar_resultados
parametros=aba=jurisprudencia&realizando_pesquisa=1&pagina_atual=1&q_palavra_chave=dano+moral&conteudo_busca=ementa_completa
```

## Dados Retornados

O envelope possui `responseHeader.params`, `response.numFound`,
`response.docs`, facets e highlighting. As facets observadas incluem orgao,
origem, relator/redator, ano, classe, assunto, tribunal, tipo de processo,
mes/ano de publicacao e data de publicacao.

## Implementacao 2026-08-11

`TjrsSolrProvider` envia o formulario legado, preservando os separadores da
query interna `parametros`, e normaliza os documentos retornados pelo envelope
SOLR. O content-type legado nao e usado como decisao de parser: o corpo e
validado como JSON. Facets, highlighting e o item bruto permanecem disponiveis.

## Decisao Tecnica

O provider deve decodificar explicitamente ISO-8859-1, preservar facets e
highlighting em `raw_metadata`, normalizar documentos para `CanonicalDecision`
e manter links de processo/documento fornecidos pelo frontend. Ainda faltam
fixtures de vazio, pagina seguinte, detalhe e inteiro teor.

Busca e paginacao ja possuem parser e testes offline; detalhe e inteiro teor
continuam deliberadamente fora do contrato executavel.

## Uso pelo MCP

O agente pode usar `tjrs_solr` para pesquisa textual, numero de processo e
intervalo de publicacao. Deve preservar `numFound`, `start`, facets,
highlighting, `SourceTrace` e o estado de completude da pagina. A resposta deve
informar que detalhe e inteiro teor ainda nao estao validados e que o header
`text/html` observado nao altera o fato de o corpo ser JSON.

## Proximos passos

1. adicionar fixture de resposta vazia e pagina seguinte;
2. validar rotas publicas de detalhe e inteiro teor sem controle de acesso;
3. mapear filtros de faceta somente depois de reproduzir payload e retorno;
4. executar teste live opt-in com termo especifico e `page_size` pequeno.

## Validacao live 2026-08-11

- O POST legado respondeu HTTP 200 com JSON, embora o content-type seja `text/html; charset=iso-8859-1`.
- `response.numFound` foi 612.403, com 10 documentos, facets, highlighting, paginas e query no envelope.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fonte Oficial

- [Busca de jurisprudencia do TJRS](https://www.tjrs.jus.br/buscas/jurisprudencia/)
