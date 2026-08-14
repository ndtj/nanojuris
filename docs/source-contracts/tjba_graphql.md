# TJBA - Jurisprudencia GraphQL

Status atual: `implemented`; busca GraphQL e inteiro teor publico possuem
provider, fixtures sanitizadas e testes de contrato.

## Contrato HTTP

- Frontend: `https://jurisprudencia.tjba.jus.br/`.
- Endpoint: `POST https://jurisprudenciaws.tjba.jus.br/graphql`.
- Tipo: `application/json`.
- Operacao observada: `filter`.

A consulta retorna `decisoes`, `relatores`, `orgaos`, `classes`, `pageCount` e
`itemCount`. Cada decisao observada trouxe data de publicacao, relator, orgao
julgador, classe, conteudo, tipo, ementa, hash e numero de processo.

## Filtros Observados

`assunto`, `numeroRecurso`, `relator`, `orgao`, `classe`, `segundoGrau`,
`turmasRecursais`, tipos de acordao/decisao, datas, ordenacao, orgaos,
relatores e classes. Os valores devem ser obtidos dos catalogos retornados,
sem inferir ids.

## Evidencia E Lacunas

Uma busca publica por assunto retornou JSON decisorio real sem login ou captcha
quando enviada com os flags padrao do frontend (`segundoGrau`,
`turmasRecursais`, tipos de decisao e `ordenadoPor`). Sem esses defaults, a
fonte pode responder HTTP 200 com erro GraphQL interno; isso e falha de
contrato, nunca resultado vazio.

## Promocao

O provider preserva o envelope GraphQL em `raw`, normaliza datas para ISO,
retorna facets em `SearchPage.aggregations` e acessa o inteiro teor por UUID.

## Validacao live 2026-08-11

- Introspection HTTP 200 confirmou `filter`, `detalharProcesso`, catalogos e os tipos `Decisao`/`DecisaoFilter`.
- Catalogos retornaram 38 orgaos, 211 relatores e 263 classes. A revalidacao
  com os defaults do frontend retornou HTTP 200, 1.236.680 itens e decisao.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fonte Oficial

- [Portal de jurisprudencia do TJBA](https://jurisprudencia.tjba.jus.br/)

## Aprofundamento Do Contrato - 2026-08-12

### Operacao de busca

Consulta GraphQL observada no endpoint oficial:

```graphql
query filter($decisaoFilter: DecisaoFilter!, $pageNumber: Int!, $itemsPerPage: Int!) {
  filter(decisaoFilter: $decisaoFilter, pageNumber: $pageNumber, itemsPerPage: $itemsPerPage) {
    decisoes { dataPublicacao relator { id nome } orgaoJulgador { id nome }
      classe { id descricao } conteudo tipoDecisao ementa hash numeroProcesso }
    relatores { key value }
    orgaos { key value }
    classes { key value }
    pageCount itemCount
  }
}
```

Variaveis minimas:

```json
{
  "decisaoFilter": {"assunto": "dano moral", "orgaos": [],
    "relatores": [], "classes": [], "segundoGrau": true,
    "turmasRecursais": true, "tipoAcordaos": true,
    "tipoDecisoesMonocraticas": true, "ordenadoPor": "dataPublicacao"},
  "pageNumber": 0,
  "itemsPerPage": 10
}
```

`pageNumber` e `itemsPerPage` sao baseados em zero e foram observados no
contrato do frontend. O provider limita a janela a 50 itens. `itemCount` e o
total de decisoes; `pageCount` permanece preservado em metadados porque a
fonte pode usa-lo como contador de pagina ou repetir o total.

### Matriz De Filtros

| Campo GraphQL | Tipo/forma observada | Estado |
| --- | --- | --- |
| `assunto` | texto livre | observado |
| `numeroRecurso` | texto/numero | observado |
| `relator` | valor de catalogo | observado |
| `orgao` | valor de catalogo | observado |
| `classe` | valor de catalogo | observado |
| `segundoGrau` | booleano | observado |
| `turmasRecursais` | booleano | observado |
| `tipoAcordaos` | lista/categoria | observado |
| `tipoDecisoesMonocraticas` | lista/categoria | observado |
| `publicacoesDe`, `publicacoesAte` | intervalo | observado |
| `dataInicial`, `dataFinal` | intervalo | observado |
| `ordenadoPor` | enum/valor do frontend | observado, valores pendentes |
| `orgaos`, `relatores`, `classes` | listas de ids/catalogo | observado |

Os catalogos de orgaos, relatores e classes devem ser carregados pela propria
resposta ou pela operacao de catalogo do frontend. Nao aceitar nomes ou ids
inventados pela camada natural-language.

### Detalhe E Inteiro Teor

Foi observada a superficie publica `GET
https://jurisprudenciaws.tjba.jus.br/inteiroTeor/{uuid}`, retornando HTML de
decisao com processo, relator, orgao e texto. Na resposta de `filter`, o campo
`hash` e um UUID aceito pela rota de inteiro teor. O provider usa esse valor
como identificador publico e preserva `id` e `sourceId` apenas como metadados.

### Estados E Erros

- HTTP 200 com `decisoes=[]` e `itemCount=0`: vazio valido.
- HTTP 200 com `errors` GraphQL: erro de contrato ou validacao, nunca vazio.
- HTTP 400/422: payload ou variavel invalida.
- HTTP 429: limite; respeitar `Retry-After` quando publicado.
- HTTP 5xx/timeout: indisponibilidade transiente, com trace.
- HTML de login/captcha no endpoint JSON: controle de acesso/contrato alterado.

### MCP E Promocao

O MCP pode usar TJBA com baixa frequencia. A resposta expoe `itemCount`,
pagina, filtros efetivos, ids de catalogo e `SourceTrace`. A promocao nao
depende de introspection em producao: a query versionada e coberta por teste
offline.

## Validacao live 2026-08-14

- O smoke integrado do `NanoJurisClient` consultou `dano moral` com uma janela
  de um resultado e recebeu HTTP 200, `1.236.680` resultados totais e uma
  decisao normalizada.
- O mesmo resultado foi usado para consultar
  `GET /inteiroTeor/{hash}`. A fonte respondeu HTTP 200 com HTML publico; o
  provider extraiu 28.346 caracteres, calculou SHA-256 e marcou o documento
  como `public` e `complete`.
- O teste live correspondente esta em
  `tests/test_tjba_graphql_live.py` e so executa quando
  `NANOJURIS_RUN_LIVE=1`. Nenhum conteudo live foi gravado no repositorio.
## Identidade

O provider representa a pesquisa de jurisprudencia do TJBA por GraphQL. A
introspection foi usada somente na pesquisa de contrato; o runtime usa query
versionada e falha explicitamente diante de `errors` GraphQL.

## Dados

Os dados juridicos observados incluem decisao, ementa, conteudo, processo,
classe, relator, orgao, tipo, hash e data de publicacao. Facets e catalogos
devem permanecer em metadados brutos.

## Implementacao Runtime

`TjbaGraphqlProvider` envia os defaults exigidos pelo frontend, converte datas
para ISO, preserva facets, carrega catalogos oficiais e consulta o inteiro teor
publico por UUID. Fixtures ficam em `tests/fixtures/` e nao contêm respostas
reais ou dados pessoais desnecessarios.

## Proximos passos

- [x] Fixture GraphQL de sucesso e vazio.
- [x] Fixture de catalogo e detalhe.
- [x] Classificacao de erros HTTP e GraphQL.
- [x] Teste live opt-in de busca e inteiro teor publico.
- [ ] Revalidar vazio e pagina seguinte em monitoramento live controlado.

## MCP

O MCP deve usar a fonte somente apos essas fixtures e expor total, pagina,
filtros, catalogos e SourceTrace.
