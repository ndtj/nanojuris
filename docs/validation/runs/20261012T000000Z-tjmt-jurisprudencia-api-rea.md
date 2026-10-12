# TJMT Jurisprudência API — revalidação REA

- Data: 2026-10-12
- Portal oficial: `https://jurisprudencia.tjmt.jus.br/`
- Evidence ID: `ev_60c9904c4ef3f7f424fbdae56ab2d181586a81e98929f6bc4356723cabec7207`

## Observação controlada

A rota oficial `/consulta/judicial` carregou a SPA em HTTP 200. A captura de
rede observou os endpoints públicos de catálogo (`/jurisprudencia/thesaurus` e
`/jurisprudencia/consulta/ultima-atualizacao-pje`) e confirmou que a busca é
`GET /jurisprudencia/consulta`, com header público `token` e parâmetros
`indicePagina`, `quantidadePagina`, `tipoConsulta`, `termoDeBusca`, `tipoBusca`,
`OrdenarPor`, `Decrescente`, `thesaurus` e `exibirArquivados`.

Em chamada direta controlada ao endpoint oficial, tanto os parâmetros do bundle
quanto os parâmetros do provider retornaram HTTP 504 em aproximadamente 15,6 s.
O provider deve classificar esse estado como `SourceUnavailableError`; não deve
fabricar uma página vazia nem afirmar que houve resultado real nessa rodada.

## Conclusão

O provider foi alinhado ao contrato atual da SPA, incluindo expressão booleana,
ordenação, filtros de número/relator/órgão e indicador de arquivados. A fonte
permanece temporariamente indisponível no backend, apesar de o portal estar
publicado.
