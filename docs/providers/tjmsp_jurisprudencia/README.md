# tjmsp_jurisprudencia

## Identidade

- Fonte oficial: [Pesquisa de Jurisprudência TJMSP](https://jurisprudencia-client.tjmsp.jus.br/).
- Entrada institucional: [Pesquisa avançada](https://www.tjmsp.jus.br/jurisprudencia-do-tjmsp-pesquisa-avancada/).
- Rota legada vinculada pela página oficial: `https://ww2.tjmsp.jus.br/Jurisprudencia`.
- Frontend/API observados no material oficial: `https://jurisprudencia-client.tjmsp.jus.br/`
  e `https://api-jurisprudencia.tjmsp.jus.br/v1/`.
- Autoridade: `TJMSP`.
- Ramo: `military`; escopo pretendido: segundo grau.
- Estado: candidato, diagnóstico opt-in.

## Estado de acesso

A entrada do frontend e o endpoint público observado no bundle retornaram HTTP
403 nas chamadas bounded. A rota legada vinculada pelo portal institucional não
resolveu no DNS no momento da verificação. A resposta 403 é um controle de
acesso, não uma busca vazia. O adapter preserva esse estado como
`AccessControlRequiredError`; não usa cookies, tokens, sessão humana, proxy ou
bypass e não interpreta a resposta como vazio.

## Contrato alternativo observado

O frontend oficial documenta a existência de uma API de jurisprudência e dos
seguintes filtros: palavra-chave, NPU, número de controle, órgão julgador,
relator, espécie e tema/índice. O endpoint
`GET /v1/tema/retornaRegistrosAtivos` foi identificado como rota de dados, mas
não foi possível observar um JSON de resultados devido ao HTTP 403. Portanto,
nenhum parser ou filtro é promovido com base apenas no nome da rota. A evidência
reproduzível está em
`docs/provider-discovery/tjmsp-jurisprudencia-api-live-recheck-20260910.json`.

Enquanto a API não entregar uma resposta pública replayável, o provider
continua diagnóstico, fora da busca federada e sem alegação de cobertura.

Evidência e contato oficial devem ser registrados antes de qualquer promoção.
