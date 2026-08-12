# TJMG - Espelho De Acordao

Status atual: `blocked_or_inconclusive` para busca automatizada.

## Identidade Da Fonte

- Tribunal: Tribunal de Justica do Estado de Minas Gerais.
- Formulario oficial: `https://www5.tjmg.jus.br/jurisprudencia/formEspelhoAcordao.do`.
- Busca por numero: `/jurisprudencia/pesquisaNumeroCNJEspelhoAcordao.do`.
- Busca por palavras: `/jurisprudencia/pesquisaPalavrasEspelhoAcordao.do`.

## Contrato Observado

A ajuda oficial documenta pesquisa de espelho de acordao, consulta por numero
CNJ, consulta textual e acesso ao inteiro teor. O formulario apresenta campos
juridicos suficientes para uma futura ficha de provider.

## Diagnostico De Acesso

A busca textual testada com termo juridico retornou HTTP 401 e pagina de
captcha. O NanoJuris nao deve automatizar ou contornar essa etapa. A ajuda e o
formulario comprovam a existencia da fonte, mas nao comprovam contrato live
reproduzivel.

Classificacao: `blocked_control`, evidencia `B`.

## Promocao Futura

Somente promover com uma superficie oficial que retorne resultado sem captcha
ou com fixture obtida de fluxo publico permitido. Nao versionar tokens,
cookies, credenciais ou dados de desafio.

## Validacao live 2026-08-11

- O formulario respondeu HTTP 200 e confirmou rotas por numero CNJ e por palavras, com filtros ricos.
- Busca textual limpa com `dano moral` respondeu HTTP 401 pedindo codigo/captcha; nao houve tentativa de contorno.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fontes Oficiais

- [Formulario de espelho de acordao](https://www5.tjmg.jus.br/jurisprudencia/formEspelhoAcordao.do)
- [Ajuda da pesquisa](https://www5.tjmg.jus.br/jurisprudencia/ajuda.do)
## Dados E Filtros

A fonte possui duas superficies distintas: pesquisa por numero CNJ e pesquisa por palavras/espelho de acordao. A ajuda/formulario indicam campos de numero, palavras, classe, orgao, relator, periodo e acesso ao inteiro teor, mas os names, payloads, paginacao e schema de resultado nao foram reproduzidos. A resposta 401/captcha nao deve ser usada para inferir campos retornados.

## MCP

O MCP deve classificar TJMG como blocked_control e nao tentar busca textual, resolver captcha ou reaproveitar tokens. Somente uma superficie oficial sem desafio ou uma fixture publica legitimamente obtida pode promover esta fonte.
