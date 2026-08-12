# CNJ - Informativos De Jurisprudencia

Status atual: `implemented` para catalogo HTML e documento PDF sob demanda.

## Implementacao Atual

- Provider: `src/nanojuris/providers/cnj_jurisprudencia.py`.
- Busca: `GET /jurisprudencia` com `argumento`, `numero`, datas e `page`.
- Documento: PDF oficial baixado somente por `get_document` com URL retornada
  em `raw.document_url`; os bytes, tamanho e SHA-256 sao preservados.
- Fixture: `tests/fixtures/cnj_jurisprudencia_results.html`.
- Testes: `tests/test_cnj_jurisprudencia.py`.
- Validacao live em 2026-08-12: HTTP 200, tabela HTML com edicao, data,
  resumo e links oficiais para PDF.
- O provider continua sendo curado/documental: nao representa a busca geral
  de acordaos do CNJ.

## Identidade Da Fonte

- Orgao: Conselho Nacional de Justica.
- Categoria: jurisprudencia administrativa curada e informativos oficiais.
- Portal: `https://atos.cnj.jus.br/jurisprudencia`.
- Formato principal: HTML paginado com links para PDF oficial.

Esta fonte nao substitui a consulta geral de processos ou o Banco Nacional de
Precedentes. O provider deve identifica-la como informativo curado do CNJ.

## Contrato HTTP Observado

Consulta sem login:

```text
GET https://atos.cnj.jus.br/jurisprudencia
```

Paginacao:

```text
GET /jurisprudencia?page=2
```

Filtros observados no formulario:

```text
numero
ano
argumento
dat_publicacao_inicio
dat_publicacao_fim
```

Exemplos reproduzidos em sessao limpa:

```text
GET /jurisprudencia?numero=10
GET /jurisprudencia?argumento=cartorios
GET /jurisprudencia?dat_publicacao_inicio=01/01/2026&dat_publicacao_fim=31/12/2026
```

Todas as consultas retornaram HTTP 200 e uma tabela HTML com tipo, numero,
data, ementa/resumo e links para arquivos no caminho `/files/` do mesmo host.

## Campos Observados

Cada linha do resultado possui:

- tipo, normalmente `Informativo de Jurisprudencia`;
- numero do informativo;
- data de publicacao;
- ementas ou itens resumidos do informativo;
- URL oficial do PDF.

O PDF e a fonte primaria do texto integral do informativo. A tabela pode
conter quebras de linha, entidades HTML e mais de um item por documento.

## Mapeamento Canonico

- `source`: `cnj`.
- `source_system`: `cnj_informativos`.
- `source_id`: combinacao estavel de numero, data e URL do PDF.
- `decision_type`: `informativo_jurisprudencia`.
- `court`: `CNJ`.
- `title`: tipo e numero do informativo.
- `published_at`: data da tabela, quando parseavel.
- `summary`: itens da coluna de ementa/resumo.
- `document_url`: link oficial do PDF.
- `raw`: linha HTML e metadados originais.

O provider nao deve converter um item resumido em decisao individual nem
inventar numero de processo, relator ou orgao julgador quando esses campos nao
estiverem no informativo.

## Limites E Riscos

- A pagina e HTML server-side; o parser deve tolerar alteracoes de classes CSS
  e localizar a tabela por cabecalhos sem depender de indices visuais.
- O filtro `argumento` retorna informativos que contem o termo em algum
  conteudo indexado; nao significa que exista um acordao individual filtrado.
- O PDF deve ser baixado somente sob demanda ou por sincronizacao explicita,
  com timeout, limite de bytes e cache por URL.
- O conteudo pode incluir nomes de partes ou terceiros em decisoes resumidas;
  preservar a fonte oficial e respeitar as regras de uso e publicidade do CNJ.

## Fixtures E Testes Necessarios

- fixture HTML de uma pagina com 10 linhas e paginacao;
- fixture de filtro por `numero`;
- fixture de filtro textual por `argumento`;
- fixture sem resultados;
- parser de data brasileira e itens numerados;
- validacao de URL absoluta e host oficial;
- teste de link PDF inexistente ou resposta nao-PDF;
- teste de paginacao sem baixar PDFs em CI.

## Uso Via MCP

O MCP pode usar esta fonte para perguntas como:

- quais informativos do CNJ tratam de um termo;
- quais itens foram publicados em um intervalo;
- qual PDF oficial documenta o item encontrado.

O resultado deve declarar `CNJ informativos`, data da consulta, pagina/filtros
e URL do PDF. Para afirmar uma tese ou detalhe de caso, o agente deve abrir o
documento oficial e citar o informativo correspondente.

## Promocao Para Provider

- [ ] versionar fixture HTML pequena;
- [ ] implementar parser offline;
- [ ] implementar filtros e paginacao;
- [ ] preservar URL e itens completos;
- [ ] adicionar teste opt-in do HTML e de um PDF pequeno;
- [ ] declarar a capacidade como conteudo curado, nao como busca geral de
  acordaos.

## Validacao live 2026-08-11

- GET com `argumento=cartorios` respondeu HTTP 200 com tabela HTML, ementas/resumos e links PDF oficiais.
- A rota continua documental e paginada; nao foi promovida a busca geral de acordaos.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fontes Oficiais

- [Consulta de jurisprudencia do CNJ](https://atos.cnj.jus.br/jurisprudencia)
- [Portal CNJ](https://www.cnj.jus.br/)

## Aprofundamento Do Contrato - 2026-08-12

### Filtros E Resposta

Os controles publicos confirmados sao `numero`, `ano`, `argumento`, `data de
inicio` e `data fim`. Os nomes exatos dos parametros ja observados no HTML sao
`numero`, `ano`, `argumento`, `dat_publicacao_inicio` e
`dat_publicacao_fim`; valores de data aparecem no formato brasileiro na
interface. A pagina usa `page` para navegacao. O tamanho maximo e a ordenacao
nao foram publicados e permanecem pendentes.

Cada linha pode conter tipo, numero, data, ementa/resumo e link para PDF
oficial. O detalhe/PDF e um documento do informativo, nao uma decisao individual
nem prova isolada de tese vinculante. HTTP 200 com tabela vazia e vazio valido;
HTML sem tabela, erro de servidor ou link PDF nao-PDF devem ser classificados e
preservados no trace.

### Uso Via MCP

O agente deve perguntar pelos filtros quando necessario e dizer explicitamente
`CNJ - Informativos de Jurisprudencia`. Deve retornar a edicao, data, item,
resumo, URL oficial e, quando aberto, o hash/tamanho do PDF. Nao deve afirmar
que o CNJ informou um acordao individual quando a fonte trouxe apenas sintese
editorial.

## Proximos Passos

Criar fixtures HTML de pagina inicial, filtro por numero, argumento, intervalo,
vazio e link PDF; implementar parser tolerante a tabela e paginacao; testar
download sob demanda com limite de bytes; manter a capacidade como conteudo
curado.
