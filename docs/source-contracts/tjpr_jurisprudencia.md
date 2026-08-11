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
