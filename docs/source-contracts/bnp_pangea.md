# `bnp_pangea`

## Identidade

- Fonte oficial: API publica usada pelo frontend Pangea/Banco Nacional de
  Precedentes.
- Categoria: `qualified_precedents`.
- Familia tecnica: `api_publica_precedentes`.
- Uso preferencial: precedentes qualificados, temas, teses e processos
  paradigma.
- Nivel atual esperado: 4.

## Contrato conhecido

O provider declara `GET /parametros`, `GET /sugestoes`, `POST /precedentes` e
`GET /precedentes/{id}/decisoes`. Retorna precedentes, especie, tribunal,
questao, tese, status, agregacoes e processos paradigma.

## Pontos fortes

- API JSON publica, sem scraping HTML no fluxo principal.
- Catalogo de orgaos e especies.
- Boa fonte para precedentes qualificados e teses nacionais.

## Lacunas a aprofundar

- Mapear rejeicoes HTTP 400 por combinacao de texto, tribunal e especie.
- Documentar payload completo de filtros e agregacoes.
- Cobrir melhor sugestoes/catalogo para consultas curtas.
- Separar claramente precedentes qualificados de jurisprudencia decisoria comum.

## MCP e agentes

Recomendacao: usar quando a pergunta envolver temas, precedentes, teses
qualificadas, repetitivos, repercussao geral, IAC ou IRDR. Para busca livre como
`idpj`, o agente deve preferir fontes de jurisprudencia decisoria antes do BNP.

## Fixtures esperadas

- catalogo de parametros;
- busca com multiplas especies;
- rejeicao HTTP 400;
- decisoes vinculadas a precedente.

## Validacao live 2026-08-11

O catalogo publico respondeu com orgaos STF/STJ e especies RG/RR. A busca com
`ICMS` sem orgao/especie retornou HTTP 400 (`Requisicao invalida`), enquanto a
mesma consulta com `courts=["STF", "STJ"]` e `types=["RG", "RR"]` retornou HTTP
200 e total observado de 100. O provider deve usar catalogo e filtros validos
antes de classificar a fonte como indisponivel.

## Validacao live 2026-08-30

Confirmado que `/precedentes` exige `orgaos` **e** `tipos` nao vazios (cada um
sozinho ainda retorna HTTP 400). O provider passou a ler `/parametros` uma vez
por instancia e preencher ambos com o catalogo completo quando a consulta nao os
informa; `search("responsabilidade civil")` sem filtros retornou HTTP 200 com
total 1963. Nenhum endpoint publico exige login: `bnp-sempj.pdpj.jus.br` (novo
backend autenticado) nao e usado.

Veja a matriz completa em
[live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/live-validation-2026-08-11.md).

## Dados retornados

O provider preserva a resposta estruturada do catalogo e da busca em `raw`,
incluindo identificador, orgao, especie, numero, tese, ementa, status,
atualizacao e agregacoes quando presentes. Decisoes vinculadas sao uma
operacao separada e nao sao tratadas como inteiro teor automatico.

## Proximos passos

- [ ] Versionar uma resposta publica de busca valida com multiplas especies.
- [ ] Versionar uma resposta vazia e uma rejeicao HTTP 400 sanitizadas.
- [ ] Confirmar campos de agregacao e filtros adicionais antes de ampliar o
  contrato de pesquisa.

## Aprofundamento De Rotas E Filtros - 2026-08-12

A interface publica atual do Pangea/BNP confirma pesquisa textual com operadores
de obrigatoriedade, frase exata e exclusao. Os filtros visiveis sao tribunais,
especies e intervalo de data de atualizacao. A plataforma tambem possui painel
estatistico e detalhes de precedente; essas superficies nao devem ser
confundidas com a lista de resultados textuais.

### Contrato Observado

Rotas usadas pelo provider:

```text
GET  https://pangeabnp.pdpj.jus.br/api/v1/parametros
GET  https://pangeabnp.pdpj.jus.br/api/v1/sugestoes?texto=<termo>
POST https://pangeabnp.pdpj.jus.br/api/v1/precedentes
GET  https://pangeabnp.pdpj.jus.br/api/v1/precedentes/{id}/decisoes
```

O filtro enviado pelo provider possui o seguinte contrato semantico:

```json
{
  "filtro": {
    "buscaGeral": "ICMS",
    "todasPalavras": null,
    "quaisquerPalavras": null,
    "semPalavras": null,
    "trechoExato": null,
    "atualizacaoDesde": null,
    "atualizacaoAte": null,
    "cancelados": false,
    "ordenacao": null,
    "nr": null,
    "pagina": 1,
    "tamanhoPagina": 20,
    "orgaos": ["STF", "STJ"],
    "tipos": ["RG", "RR"]
  }
}
```

Campos de filtro aceitos pelo modelo do provider: `text`, `all_words`,
`any_words`, `without_words`, `exact_phrase`, `updated_from`, `updated_to`,
`include_cancelled`, `order_by`, `number`, `page`, `page_size`, `courts` e
`types`. O catalogo de parametros deve ser consultado antes de montar
`courts` e `types`; uma consulta textual sem orgao/especie pode ser rejeitada
com HTTP 400 sem significar indisponibilidade da fonte.

### Interpretacao E Limites

- `precedentes` e a busca de precedentes qualificados; nao substitui a busca
  geral de acordaos dos tribunais.
- `precedentes/{id}/decisoes` e uma expansao de decisoes vinculadas ao
  precedente, nao um endpoint generico de inteiro teor.
- O retorno deve preservar total, pagina, tamanho, especie, orgao, numero,
  tese, ementa, status e links de decisoes quando presentes.
- A camada MCP deve expor catalogo, busca e decisoes como operacoes distintas,
  informando ao agente quando a consulta foi restringida por especie.
- Fixtures obrigatorias: catalogo, busca valida multi-filtro, HTTP 400 por
  filtro insuficiente, pagina vazia e detalhe com decisoes vinculadas.
