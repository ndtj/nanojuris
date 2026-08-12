# TJPR - Pesquisa De Jurisprudencia

Status atual: `candidate_ready`; provider HTML pendente de fixture e parser.

## Contrato Observado

- Rota: `GET https://portal.tjpr.jus.br/jurisprudencia/publico/pesquisa.do?actionType=pesquisarRefinado&filtro=true`.
- Resposta: HTML publico.
- Evidencia: HTTP 200 em sessao limpa, sem captcha/login no teste inicial.

A pagina de resultado exibiu identificadores processuais, relator, orgao
julgador, ementa, acordao, volume total e paginacao. A pesquisa deve preservar
os links oficiais retornados, sem reconstruir URLs de detalhe por heuristica.

## Escopo De Fixture

Usar termos de areas diferentes, como `dano moral`, `plano de saude` e
`execucao fiscal`, e registrar uma resposta vazia. A fixture deve manter o
charset real da pagina e separar resultado, paginacao e mensagens de filtro.

## Promocao

Implementar parser offline primeiro, com testes para sucesso, vazio, pagina
seguinte e alteracao de markup. O fetcher live somente entra depois que o
contrato de detalhe e inteiro teor estiver confirmado.

## Validacao live 2026-08-11

- A consulta refinada respondeu HTTP 200 HTML com ementa, relator, orgao, processo e paginacao.
- A proxima etapa e fixture/parser; links de detalhe devem ser preservados da resposta, sem reconstrucoes heuristicas.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fonte Oficial

- [Pesquisa publica de jurisprudencia TJPR](https://portal.tjpr.jus.br/jurisprudencia/publico/pesquisa.do?actionType=pesquisarRefinado&filtro=true)

## Aprofundamento Do Contrato - 2026-08-12

### Superficie E Pagina

O resultado oficial apresenta, na mesma consulta, o acervo do TJPR e uma
secao de decisoes traduzidas da Corte IDH. Na observacao atual, a pagina
principal informa faixa de ate 50 registros do TJPR, ate 40 registros na
secao do tribunal e ate 10 registros da Corte IDH. Esses numeros sao limites
de apresentacao observados, nao autorizacao para coleta sem limite.

O detalhe segue links oficiais no formato observado:

```text
GET https://portal.tjpr.jus.br/jurisprudencia/j/{identificador}/{slug}
```

`{slug}` e o identificador devem ser extraidos do HTML. O provider nao deve
montar o slug nem presumir que todo resultado tem inteiro teor.

### Filtros Publicos

| Filtro exibido | Escopo | Parametro HTTP |
| --- | --- | --- |
| texto/ementa | pesquisa geral | nome exato ainda pendente |
| Classe | TJPR | nome exato ainda pendente |
| Relator | TJPR | nome exato ainda pendente |
| Comarca | TJPR | nome exato ainda pendente |
| Orgao Julgador | TJPR | nome exato ainda pendente |
| Assunto | TJPR | nome exato ainda pendente |
| Ano da publicacao | TJPR | nome exato ainda pendente |
| Pais | Corte IDH | nome exato ainda pendente |
| Tema | Corte IDH | nome exato ainda pendente |
| Juiz | Corte IDH | nome exato ainda pendente |
| Juiz e Cargo | Corte IDH | nome exato ainda pendente |

Os rotulos acima foram observados na interface e no resultado oficial. Antes
do provider, um HAR ou fixture de formulario deve fechar nomes, codificacao de
multivalores, ordenacao, pagina e acao de refinamento.

### Campos Do Resultado

Extrair somente quando presentes: tipo, numero do processo, relator e cargo,
orgao julgador, comarca, data de julgamento, classe, assunto, ementa,
conteudo/decisao, indicador de segredo e URL de detalhe. Preservar o HTML da
linha e o link original em `raw`; nao confundir ementa editorial com inteiro
teor.

### Estados E Limites

- HTTP 200 com total e lista vazia: vazio valido.
- Resultado com "Conteudo pendente de analise e liberacao": registro publico
  sem texto; nao tentar inferir o conteudo.
- Redirect para sessao expirada, 403, captcha ou HTML sem tabela: acesso
  controlado/contrato alterado.
- Paginacao e ordenacao devem ser extraidas dos links/controles retornados,
  sem calcular offsets por estimativa.
- O grande volume exibido pelo portal exige pagina pequena e rate limit local.

### MCP E Promocao

O MCP deve declarar separadamente resultados TJPR e Corte IDH, registrar filtros
efetivos, faixa retornada, total e links oficiais. Promover somente depois de
fixtures de busca textual, filtro, vazio, pagina seguinte, detalhe e resultado
com segredo/sem conteudo.
## Dados

O resultado observado possui tipo, processo, relator, cargo, orgao, comarca,
data de julgamento, ementa/conteudo e links oficiais. Resultados da Corte IDH
devem manter tipo e origem separados dos resultados TJPR.

## MCP

O MCP deve separar TJPR e Corte IDH, apresentar total/faixa, filtros efetivos e
links oficiais, e omitir conteudo pendente de liberacao como se fosse inteiro
teor.

## Proximos passos

Fechar fixture de formulario com nomes dos parametros, multivalores,
ordenacao, pagina, vazio, detalhe e resultado sem conteudo. Depois implementar
parser offline antes do fetcher live.
