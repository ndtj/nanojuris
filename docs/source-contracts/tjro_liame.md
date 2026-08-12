# TJRO - LIAME E Precedentes

Status atual: `documental` para catalogo de precedentes; nao e provider geral
de acordaos.

## Identidade Da Fonte

- Portal: `https://liame.tjro.jus.br/`.
- Categoria: precedentes qualificados e catalogo tematico.
- Filtros observados: tribunal, especie, situacao e processo paradigma.

O portal tambem informa sincronizacao com BNP, STF e TPU. O mapeamento nao
confirmou uma rota publica de busca integral de acordaos do TJRO.

## Diagnostico

O probe inicial encontrou o portal e sinais de conteudo, mas classificou um
texto de interface como `access_denied`. Isso deve ser tratado como falso
positivo de diagnostico ate uma leitura semantica mais especifica, sem assumir
que o acervo esta bloqueado.

## Promocao

Criar primeiro um adapter de `CanonicalPrecedent` com fixture de catalogo,
filtros, vazio e detalhe. Buscar acordaos somente quando uma rota oficial de
resultados for comprovada separadamente.

## Validacao live 2026-08-11

- O portal LIAME respondeu HTTP 200 e exibiu sinais de precedentes/processos.
- A chamada nao confirmou uma busca geral de acordaos; o escopo deve permanecer em catalogo de precedentes ate haver rota de resultados.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/lucmolero/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fonte Oficial

- [LIAME TJRO](https://liame.tjro.jus.br/)
## Contrato E Filtros

A superficie LIAME confirmou catalogo de precedentes, com filtros de tribunal, especie, situacao e processo paradigma. Nao foi confirmada rota de busca geral de acordaos, nem metodo, payload, pagina, ordenacao ou detalhe por HTTP limpo. O contrato de eventual documento deve ser separado do catalogo.

## Dados E MCP

O adapter futuro deve retornar CanonicalPrecedent com especie, situacao, processo paradigma, tribunal, tese/ementa quando publicada e URL oficial. O MCP pode usar a fonte somente como catalogo de precedentes e deve dizer que ela nao representa o acervo geral de acordaos.

## Proximos Passos

Fechar fixture de catalogo com resultado, vazio, filtro e detalhe. So criar provider depois de confirmar schema, ids estaveis e limites da consulta.
## MCP

Usar somente como catalogo de precedentes e declarar que nao representa o
acervo geral de acordaos. Manter a busca geral fora do roteamento ate contrato
de resultados.

## Contrato

Confirmados apenas portal e filtros de catalogo: tribunal, especie, situacao
e processo paradigma. Metodo, payload, pagina, ordenacao e detalhe continuam
pendentes.

## Dados

O futuro CanonicalPrecedent deve preservar especie, situacao, processo
paradigma, tribunal, tese/ementa e URL oficial quando publicados.
