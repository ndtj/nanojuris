# CNJ - Informativos De Jurisprudencia

Status atual: `candidate_ready` para provider HTML/PDF de informativos curados.

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

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fontes Oficiais

- [Consulta de jurisprudencia do CNJ](https://atos.cnj.jus.br/jurisprudencia)
- [Portal CNJ](https://www.cnj.jus.br/)
