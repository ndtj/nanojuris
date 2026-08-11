# TJPE - Consulta Jurisprudencia

Status atual: `candidate_ready` para fixture, parser e provider REST.

## Identidade Da Fonte

- Tribunal: Tribunal de Justica do Estado de Pernambuco.
- Portal institucional: `https://portal.tjpe.jus.br/web/jurisprudencia/tjpe-e-turmas-recursais`.
- Aplicacao oficial: `https://consultajurisprudencia.app.tjpe.jus.br/`.
- Categoria: jurisprudencia estadual, acordaos e decisoes.

## Contrato HTTP Observado

A aplicacao Angular publica no bundle do frontend os seguintes recursos REST:

- `GET /api/v1/jurisprudencias`
- `GET /api/v1/classes`
- `GET /api/v1/assuntos`
- `GET /api/v1/relatores`
- `GET /api/v1/unidades-judiciais`
- `GET /api/v1/processo/{codigoProcesso}/{npuSemFormatacao}`

Base observada:

`https://consultajurisprudencia.app.tjpe.jus.br`

Consulta minima:

```text
GET /api/v1/jurisprudencias?page=0&size=20
```

Filtros observados no frontend:

```text
pesquisaLivre.contains
npuSemFormatacao.equals
numAntigo.equals
dataJulgamento.greaterThanOrEqual
dataJulgamento.lessThanOrEqual
relator.in
assuntoCNJ.in
classeCNJ.in
orgaoJulgador.in
meioTramitacao.in
tipoSentenca.in
```

Ordenacao usa o padrao Spring Data, por exemplo:

`sort=dataJulgamento,desc`

## Evidencia De Dados

Em sessao HTTP sem login, a rota de jurisprudencias retornou HTTP 200 JSON com:

- `X-Total-Count` e links de paginacao;
- numero CNJ em `npu` e versao sem formatacao;
- classe e descricao da classe;
- relator e orgao julgador;
- data de julgamento e data de publicacao;
- `textoEmenta`, quando disponivel;
- `textoAcordao` ou `textoDecisao`, quando publicado;
- identificador `chave` e codigo do processo.

Uma consulta com `tipoSentenca.in=A` e `assuntoCNJ.in=9098` retornou HTTP 200,
656 registros e objetos com ementa e texto de acordao. As rotas de catalogo
tambem retornaram JSON real: classes, assuntos, relatores e unidades judiciais.

## Limites E Riscos

- O ambiente de probe apresentou erro de validacao da cadeia TLS para o host da
  aplicacao; o teste diagnostico usou `verify=False` somente para confirmar o
  contrato publico. Isso nunca deve ser usado no provider ou em producao.
- A fixture e o teste live devem voltar a validar o certificado normalmente em
  ambiente com CA atualizada.
- O filtro de texto livre apresentou erro 500 em algumas combinacoes isoladas;
  o provider deve validar a combinacao de filtros e registrar erro de contrato,
  sem transformar uma resposta 500 em busca vazia.
- A API lista documentos recentes e pode devolver `textoEmenta` nulo em alguns
  registros, mantendo `textoAcordao` ou `textoDecisao`.
- O endpoint de processo pode retornar um pacote vazio quando os identificadores
  nao correspondem ao sistema processual consultado.

## Promocao Para Provider

Antes de implementar:

- capturar fixture JSON de sucesso com ementa;
- capturar fixture JSON de sucesso com texto de acordao;
- capturar pagina vazia e erro 400/500;
- validar filtros `assuntoCNJ`, `classeCNJ`, `tipoSentenca` e periodo;
- validar paginacao e `X-Total-Count`;
- usar verificacao TLS padrao;
- mapear `chave` para `source_id` e preservar os campos brutos;
- criar teste live opt-in com limite pequeno e rate limit.

## Uso Via MCP

O agente deve declarar a fonte como TJPE e informar quando a resposta possui
ementa, acordao ou decisao. O resultado deve preservar `SourceTrace`, URL,
parametros, pagina, total informado e eventuais campos nulos. A fonte nao deve
ser apresentada como consulta processual completa: o escopo deste contrato e
jurisprudencia.

## Validacao live 2026-08-11

- Com verificacao TLS padrao, o host falhou por certificado; com `verify_ssl=False` apenas para diagnostico, `/api/v1/jurisprudencias?page=0&size=2` retornou dois itens JSON ricos.
- O provider nao pode desabilitar TLS; a cadeia deve ser corrigida no ambiente antes da implementacao.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fontes Oficiais

- [TJPE - TJPE e Turmas Recursais](https://portal.tjpe.jus.br/web/jurisprudencia/tjpe-e-turmas-recursais)
- [Aplicacao oficial de Consulta Jurisprudencia](https://consultajurisprudencia.app.tjpe.jus.br/)
- [Pesquisa institucional de jurisprudencia do TJPE](https://portal.tjpe.jus.br/web/jurisprudencia/busca)
