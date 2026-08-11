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
