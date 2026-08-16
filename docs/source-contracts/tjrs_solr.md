# TJRS - Jurisprudencia AJAX/SOLR

Status atual: `implemented`; busca textual JSON/SOLR e paginacao por offset
possuem contrato reproduzido, fixture offline e evidencia live recente.
Detalhe e inteiro teor continuam explicitamente fora do contrato executavel.

## Identidade e escopo

- Fonte oficial: portal de jurisprudencia do Tribunal de Justica do Rio Grande
  do Sul.
- Categoria: `court_jurisprudence`.
- Familia tecnica: formulario AJAX legado com resposta SOLR-like em JSON.
- O provider cobre busca textual, numero de processo, metadados, facets e
  highlighting retornados pelo indice.
- Nao representa consulta processual nem anuncia inteiro teor.

## Contrato HTTP

- Portal: `https://www.tjrs.jus.br/novo/buscas-solr/?aba=jurisprudencia`.
- Iframe: `https://www.tjrs.jus.br/buscas/jurisprudencia/`.
- Endpoint: `POST https://www.tjrs.jus.br/buscas/jurisprudencia/ajax.php`.
- Tipo observado: corpo JSON com header legado
  `text/html; charset=iso-8859-1`.
- Payload minimo reproduzido:

```text
action=consultas_solr_ajax
metodo=buscar_resultados
parametros=aba=jurisprudencia&realizando_pesquisa=1&pagina_atual=1&q_palavra_chave=dano+moral&conteudo_busca=ementa_completa
```

`page` e convertido para `pagina_atual`. `page_size` limita a janela local
normalizada; `response.numFound` e preservado como total remoto.

## Dados e rastreabilidade

O envelope possui `responseHeader.params`, `response.numFound`,
`response.start`, `response.docs`, facets e highlighting. A identidade usa,
em ordem, `cod_ementa`, `numero_processo` ou `_version_`; ausencia desses
campos gera `ParserContractChangedError`, nunca um ID baseado no indice.

O `SourceTrace` registra endpoint, URL final, status HTTP, content-type,
SHA-256 dos bytes recebidos, tamanho em bytes e `retrieval_status`. As datas
de atualizacao, julgamento e publicacao sao mantidas em campos distintos.

## Filtros e paginacao

Filtros implementados: termo livre, frase exata, numero, pagina e intervalo de
publicacao. Facets de orgao, origem, relator, ano, classe, assunto, tribunal,
tipo de processo e mes/ano permanecem nos metadados brutos quando retornadas;
nao sao tratados como filtros executaveis sem contrato adicional.

O modo e `offset`, com `numFound` e `start` da resposta. A completude da
janela e calculada pela relacao entre total remoto, deslocamento e quantidade
retornada.

## Fixtures e testes

- Sucesso e parser: `tests/fixtures/tjrs_solr_results.json`.
- Estados compartilhados: `tests/fixtures/provider_contracts.json`.
- Testes: `tests/test_tjrs_solr.py`.
- Cobertura: identidade estavel, datas semanticas, trace HTTP, hash, bytes,
  resposta 429 e ausencia de identificador.

## Detalhe e inteiro teor

O provider nao promove `document_url` numerica ou link legado a documento
carregado. Rotas de detalhe e inteiro teor devem ser reproduzidas em sessao
publica limpa, com fixture e teste, antes de serem expostas como capacidade.

## Uso pelo MCP e Studio

O agente pode usar `tjrs_solr` para pesquisa textual e deve receber total,
offset, facets, highlighting, trace e completude. A interface deve informar
que o resultado e de indice/ementa e que detalhe e inteiro teor nao foram
validados pelo provider.

## Validacao live

Em `2026-08-16`, a busca publica por `responsabilidade civil` respondeu com
HTTP 200, total remoto e documento normalizado. A evidencia estruturada esta
em `docs/validation/runs/20260816T070048Z-gold-wave-1-20260816.json`.

Essa rodada antecedeu a correcao que passou a incluir os metadados HTTP no
trace do TJRS; uma nova rodada deve ser usada para monitoramento posterior.

## Limitacoes e proxima promocao

- O content-type legado nao deve decidir o parser: o corpo precisa ser JSON
  validado.
- `numFound` nao garante coleta integral do corpus.
- Filtros de facets, pagina vazia e pagina posterior ainda precisam de
  amostras live adicionais.
- O provider pode atingir Gold para busca textual sem inteiro teor, desde que
  a estabilidade do contrato e da paginacao permaneça comprovada.

## Proximos passos

- Revalidar pagina vazia e pagina posterior em monitoramento live controlado.
- Mapear rotas publicas de detalhe e inteiro teor antes de anuncia-las.
