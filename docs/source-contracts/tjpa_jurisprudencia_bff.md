# `tjpa_jurisprudencia_bff`

## Identidade

- Fonte oficial: Jurisprudencia publica do TJPA.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `spa_bff_jurisprudencia`.
- URL inicial: `https://jurisprudencia.tjpa.jus.br/`.
- Status de acesso: `public` para a busca textual JSON e catalogos observados.
- Status no NanoJuris: implementado para busca textual, texto integral embutido
  quando retornado pelo BFF e catalogos; detalhe documental separado ainda nao
  promovido.

O contrato foi revalidado em 2026-08-11 a partir do portal oficial e do bundle
publico atual. A rota de resultados exige `POST`; o `GET` simples em
`/bff/api/decisoes` retorna 404 por uso incorreto do metodo.

## Contrato HTTP

### Busca textual

```text
POST https://jurisprudencia.tjpa.jus.br/bff/api/decisoes/buscar
Content-Type: application/json
```

Payload minimo reproduzido:

```json
{
  "query": "dano moral",
  "queryType": "free",
  "queryScope": "ementa",
  "page": 0,
  "size": 2,
  "sortBy": "relevancia",
  "sortOrder": "desc"
}
```

Valores observados no frontend:

- `queryType`: `free` ou `anywords`;
- `queryScope`: `ementa` ou `inteiroTeor`;
- `page`: pagina baseada em zero;
- `size`: tamanho da pagina;
- `sortBy`: `relevancia` e ordenacao temporal conforme o catalogo atual;
- `sortOrder`: `asc` ou `desc`.

Filtros opcionais expostos pelo frontend:

```json
{
  "origem": [],
  "tipo": [],
  "classe": [],
  "assunto": [],
  "relatores": [],
  "orgaoJulgadorColegiado": [],
  "dataJulgamentoInicio": "dd/MM/yyyy",
  "dataJulgamentoFim": "dd/MM/yyyy",
  "dataPublicacaoInicio": "dd/MM/yyyy",
  "dataPublicacaoFim": "dd/MM/yyyy"
}
```

Chaves opcionais sem valor devem ser omitidas na serializacao final. Os
valores de `origem` e `tipo` devem ser usados exatamente como retornados por
`/filtros`; nao inferir nomes ou ids a partir de texto livre. Esse procedimento
foi validado com uma busca que retornou resultado.

### Catalogos

```text
GET https://jurisprudencia.tjpa.jus.br/bff/api/decisoes/filtros
```

Resposta observada: HTTP 200 JSON com `message` e `data`. O objeto `data`
publica catalogos para:

- `orgaosJulgadoresColegiados`;
- `orgaosJulgadoresColegiadosTJ`;
- `orgaosJulgadoresColegiadosTurma`;
- `origens`;
- `tipos`;
- `classes`;
- `assuntos`;
- `relatores`.

### Decisoes recentes

```text
GET https://jurisprudencia.tjpa.jus.br/bff/api/decisoes/recentes
```

Parametros observados:

```text
dataInicio=2026-01-01T00:00:00
dataFim=2026-08-11T23:59:59
origem=Tribunal de Justica do Estado do Para
tipo=Acordao
page=0
size=2
```

Esta rota e uma listagem temporal, nao uma busca textual. A resposta publica
`content`, `totalElements`, `totalPages`, `currentPage` e `size`, alem dos
campos decisorios. O ambiente observado informou limite tecnico de 10.000
registros; o provider deve expor esse limite e nao simular completude.

### Busca por classe e assunto

```text
POST https://jurisprudencia.tjpa.jus.br/bff/api/decisoes/pesquisar-por-classe-assunto
Content-Type: application/json
```

O frontend monta um payload separado, com `idsClasses`, `idsAssuntos`,
`origens`, `tiposDecisao`, datas em `dd/MM/yyyy`, pagina, tamanho e ordenacao.
O formato de data foi confirmado: datas ISO produziram HTTP 400 com mensagem
de formato invalido. A selecao de ids ainda precisa de fixture de sucesso;
ids arbitrarios produziram vazio ou erro e nao devem ser tratados como
contrato fechado.

### Rotas de detalhe observadas no bundle

O bundle atual tambem referencia:

- `GET /bff/api/decisoes/{id}`;
- `GET /bff/api/decisoes/processo/{numero}`;
- `GET /bff/api/decisoes/indexadas`;
- `GET /bff/api/decisoes/tema/{id}`;
- `POST /bff/api/decisoes/buscar-por-numero-processo`;
- `POST /bff/api/decisoes/buscar-por-numero-documento`.

Essas rotas foram identificadas no frontend, mas ainda precisam de chamada
publica controlada e fixture antes de serem declaradas operacionais. As rotas
diretas de detalhe por id e por processo foram testadas com identificadores
retornados pela busca e responderam HTTP 404; ficam referenciadas, mas nao
operacionais, ate localizar o contrato correto. Rotas de autenticacao,
escrita e administracao ficam fora do escopo do provider.

## Dados retornados

Resposta observada em `/buscar`:

- `content`;
- `totalElements`;
- `totalAcordaos`;
- `totalDecisoesMonocraticas`;
- `totalPages`;
- `currentPage`;
- `size`;
- `facets`;
- `consultaUtilizada`;
- `excedeuLimiteTecnico`;
- `limiteMaximo`;
- `mensagemLimiteTecnico`.

Itens de `content` expuseram campos ricos, incluindo:

- `id`;
- `numeroprocesso`;
- `tipo`;
- `pessoas`;
- `orgaojulgadorcolegiado`;
- `datadocumento`;
- `datajulgamento`;
- `sentidodecisao`;
- `textooriginal`;
- `textopuro`;
- `textoementa`;
- `ementatextopuro`;
- `temas`;
- `indexacao`;
- `resumoIA`;
- `analiseIA`;
- `lido`;
- `idstemas`.

O provider deve preservar o JSON bruto e normalizar apenas o que possuir
semantica comprovada. Nao deve fabricar relator, classe, assunto, data ou
inteiro teor ausente. Dados publicos devem permanecer disponiveis ao
consumidor, sujeitos somente a regras gerais de transporte e armazenamento do
projeto.

## Evidencia live

Em sessao HTTP limpa, sem login, cookie exportado, captcha ou bypass:

- `/filtros`: HTTP 200 JSON com catalogos de origens, tipos, classes, assuntos
  e relatores;
- `/recentes`: HTTP 200 JSON com campos decisorios e limite tecnico de 10.000;
- `/buscar` com `dano moral`, `free` e escopo `ementa`: HTTP 200 JSON com
  `content` e total tecnico de 10.000;
- `/buscar` com `indenizacao`, `anywords` e escopo `ementa`: HTTP 200 JSON;
- `/buscar` com `aposentadoria`, `free` e escopo `inteiroTeor`: HTTP 200 JSON.

Filtros de origem/tipo enviados com valores arbitrarios retornaram resposta
vazia nesta sessao. Quando os valores exatos de `origens[].origem` e
`tipos[].descricao` foram obtidos de `/filtros`, a busca retornou HTTP 200, um
resultado e total tecnico de 10.000. Filtros de classe/assunto ainda exigem
fixture de sucesso.

### Inteiro teor na busca

Quando o item retorna `textopuro`, `textooriginal`, `full_text` ou `conteudo`,
o provider preenche `JurisprudenceResult.full_text` e preserva o objeto JSON
original em `raw`. Isso e texto integral embutido na resposta de busca, nao
uma garantia de rota documental por id. O contrato informa essa diferenca ao
Studio, CLI e MCP; `document_url` so deve ser adicionado quando a fonte
retornar uma URL documental real.

## Comportamento e riscos

- O contrato e JSON, mas e exposto por um frontend SPA e pode mudar junto com
  o bundle.
- O backend aplica limite tecnico de resultados; pagina adicional nao deve
  prometer acesso acima do limite.
- A rota textual e o filtro basico origem/tipo estao comprovados; filtros de
  classe/assunto e detalhes ainda precisam de validacao independente.
- `consultaUtilizada` pode conter a consulta interna do mecanismo de busca;
  preservar somente quando for util para diagnostico e sem acoplar o parser a
  essa estrutura interna.
- Requisições devem usar rate limit, timeout, identificacao honesta do cliente
  e opt-in para testes live.
- Nao usar endpoints de escrita, administracao, autenticacao ou qualquer
  mecanismo de contorno de protecao.

## Fixtures

- [x] Bundle publico revisado e rotas atuais identificadas.
- [ ] JSON de sucesso de `/buscar` sem filtros.
- [ ] JSON de sucesso com filtros selecionados a partir de `/filtros`.
- [ ] JSON de `/filtros` com catalogos.
- [ ] JSON de `/recentes` com limite tecnico.
- [ ] JSON vazio.
- [ ] JSON de erro de validacao.
- [ ] Respostas das rotas de detalhe, processo e documento; id e processo
  atualmente retornam 404 e precisam de contrato correto.
- [ ] Fixture sem dados pessoais reais desnecessarios ao teste.

## MCP e agentes

O MCP pode oferecer uma ferramenta de pesquisa TJPA somente depois de o
provider possuir parser offline e testes de contrato. A descricao deve
informar que a fonte e publica, que a busca tem limite tecnico e que resultados
podem ser truncados pelo backend. Para perguntas de detalhe, o agente deve
usar a rota de detalhe apenas quando ela estiver validada; caso contrario,
deve retornar os campos presentes na busca e declarar a lacuna.

Mensagem operacional sugerida:

> O TJPA retornou resultados publicos estruturados. A consulta respeita o
> limite tecnico informado pela fonte; filtros e detalhes sao usados somente
> quando o contrato correspondente estiver validado.

## Validacao live 2026-08-11

- `/filtros` e `/buscar` responderam HTTP 200 JSON no envelope `{message, data}`.
- A busca confirmou `content`, totais, facets, limite tecnico e itens com processo, datas, classe, orgao, ementa, texto puro e indexacao.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Implementacao 2026-08-11

- `TjpaJurisprudenciaBffProvider` implementa `POST /bff/api/decisoes/buscar`.
- `get_catalog()` implementa `GET /bff/api/decisoes/filtros` e preserva o envelope bruto.
- O provider normaliza processo, tipo, ementa, relator, datas, classe, assunto e texto puro.
- `get_decisions()` permanece explicitamente indisponivel ate validar uma rota publica de detalhe.

## Proximos passos

- [ ] Salvar fixture pequena e representativa de `/filtros`.
- [ ] Salvar fixture de sucesso de `/buscar` sem dados pessoais desnecessarios.
- [ ] Reproduzir filtros usando valores exatos dos catalogos.
- [ ] Validar pagina, ordenacao e limite tecnico.
- [ ] Testar detalhe por id e busca por numero de processo.
- [x] Criar parser JSON offline e mapear resultados para o modelo normalizado.
- [x] Criar fixture sintética e testes de contrato.
- [ ] Validar e implementar uma rota publica de detalhe, se o contrato permanecer estavel.
