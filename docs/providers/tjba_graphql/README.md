# TJBA - Jurisprudencia GraphQL

Status atual: `candidate_ready`; provider ainda pendente de fixture e parser.

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

Uma busca publica por assunto retornou JSON decisorio real sem login ou captcha.
O detalhe de inteiro teor usa o host oficial e identificador UUID, mas ainda
precisa de fixture de detalhe, vazio, erro e paginacao antes do provider.

## Promocao

Salvar resposta GraphQL reduzida, resposta vazia e detalhe por UUID. Criar
parser offline que preserve o JSON bruto, normalize os campos canonicos e
retenha filtros/facets em `raw_metadata`.

## Validacao live 2026-08-11

- Introspection HTTP 200 confirmou `filter`, `detalharProcesso`, catalogos e os tipos `Decisao`/`DecisaoFilter`.
- Catalogos retornaram 38 orgaos, 211 relatores e 263 classes. `filter` respondeu erro interno nesta janela e precisa de revalidacao com valores aceitos.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

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
  "decisaoFilter": {"assunto": "dano moral"},
  "pageNumber": 0,
  "itemsPerPage": 10
}
```

`pageNumber` e `itemsPerPage` foram observados no contrato do frontend; o
limite maximo de itens e a indexacao da primeira pagina ainda precisam ser
confirmados por fixture. O adapter deve preservar `pageCount` e `itemCount`
como metadados da pagina, sem tratar `pageCount` como total de decisoes.

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
decisao com processo, relator, orgao e texto. O UUID ou identificador usado no
detalhe ainda nao esta exposto no fragmento minimo da operacao `filter`; por
isso o parser deve capturar o link/identificador real da resposta e nao
reconstruir a URL por posicao.

### Estados E Erros

- HTTP 200 com `decisoes=[]` e `itemCount=0`: vazio valido.
- HTTP 200 com `errors` GraphQL: erro de contrato ou validacao, nunca vazio.
- HTTP 400/422: payload ou variavel invalida.
- HTTP 429: limite; respeitar `Retry-After` quando publicado.
- HTTP 5xx/timeout: indisponibilidade transiente, com trace.
- HTML de login/captcha no endpoint JSON: controle de acesso/contrato alterado.

### MCP E Promocao

O MCP pode usar TJBA somente depois de fixture GraphQL de sucesso, vazio,
erro, pagina seguinte e detalhe. A resposta deve expor `itemCount`, pagina,
filtros efetivos, ids de catalogo e `SourceTrace`. A promocao nao depende de
introspection em producao: a query versionada deve ser pequena e coberta por
teste offline.
## Identidade

O provider candidato representa a pesquisa de jurisprudencia do TJBA por
GraphQL. A fonte continua candidata porque a introspection/catalogos foram
observados, mas a operacao de filtro apresentou erro interno na ultima janela.

## Dados

Os dados juridicos observados incluem decisao, ementa, conteudo, processo,
classe, relator, orgao, tipo, hash e data de publicacao. Facets e catalogos
devem permanecer em metadados brutos.

## Proximos passos

Salvar fixtures GraphQL de sucesso, vazio, erro, pagina e detalhe; validar
novamente a operacao filter com valores de catalogo; somente entao criar o
parser e o provider runtime.

## MCP

O MCP deve usar a fonte somente apos essas fixtures e expor total, pagina,
filtros, catalogos e SourceTrace.
