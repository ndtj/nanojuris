# CNJ - Informativos De Jurisprudencia

Status atual: `implemented` para catalogo HTML e documento PDF sob demanda.

## Implementacao Atual

- Provider: `src/nanojuris/providers/cnj_jurisprudencia.py`.
- Busca: `GET /jurisprudencia` com `argumento`, `numero`, datas e `page`.
- Documento: PDF oficial baixado somente por `get_document` com URL retornada
  em `raw.document_url`; os bytes, tamanho e SHA-256 sao preservados.
- Fixture: `tests/fixtures/cnj_jurisprudencia_results.html`.
- Fixtures de estados: `tests/fixtures/cnj_jurisprudencia_empty.html` e
  `tests/fixtures/cnj_jurisprudencia_schema_drift.html`.
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
O provider preserva os bytes do PDF e sua integridade, mas nao extrai o texto
para `CanonicalDocument.text`; portanto `supports_full_text` permanece falso.

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

- [x] versionar fixture HTML pequena: `tests/fixtures/cnj_jurisprudencia_results.html`;
- [x] versionar estados vazio e schema drift:
  `tests/fixtures/cnj_jurisprudencia_empty.html` e
  `tests/fixtures/cnj_jurisprudencia_schema_drift.html`;
- [x] implementar parser offline com detecção de vazio e schema drift;
- [x] implementar filtros e paginação por `page`;
- [x] preservar URL e itens completos no registro bruto;
- [x] adicionar testes opt-in de HTML e PDF sob demanda;
- [x] declarar a capacidade como conteúdo curado, não como busca geral de
  acórdãos.

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

## Evidência live bounded (2026-09-08)

O smoke público executou duas páginas com `cartorios`: HTTP 200, dois itens
por página, dez itens reportados, links PDF e IDs sem sobreposição. O artefato
redigido está em `docs/provider-discovery/cnj-live-20260908-transport-recheck.json`.

## Transporte compartilhado (2026-09-08)

As consultas HTML do catÃ¡logo e os downloads explÃ­citos de PDF agora passam
por `SharedHttpClient`, com allowlist CNJ, limite de 16 MB, timeout, rate limit
e circuito. Respostas 401/403/429, TLS, timeout, redirecionamento fora da
allowlist e contrato invÃ¡lido continuam estados distintos de catÃ¡logo vazio;
respostas de desafio nÃ£o sÃ£o repetidas automaticamente.

## Proximos Passos

Manter smoke live periódico de baixa frequência e revalidar o link PDF sob
demanda. A fonte permanece deliberadamente curada e não será apresentada como
busca geral de acórdãos.

## Evidencia live 2026-09-05 (ciclo 64)

Consulta limitada por `argumento=cartorios` em duas páginas retornou HTML HTTP
200 com itens e links PDF oficiais, sem sobreposição observada. O envelope
redigido está em `docs/provider-discovery/cnj-live-20260905-cycle64.json`; os
PDFs não foram baixados nesta rodada.
