# TJMT Jurisprudencia API — validacao live

- Data: 2026-08-16 17:30 UTC.
- Consulta: `transporte aereo dano moral`.
- Busca: HTTP 200, 7.578 acordaos reportados, 5 itens solicitados.
- Inteiro teor: 5/5 itens continham `Documento` HTML inline e texto extraivel.
- Pagina 2: 5 itens retornados, 4 IDs novos na comparacao imediata.
- Config publico: HTTP 200; o token foi lido em runtime e nao foi persistido.
- Hash da resposta da pagina 1: `5b64b7b8f7c89d033ac279fae45dfea905fd096a1aede9b0cdf3e47ed5092550`.
- Tamanho da resposta: 806.831 bytes.

A sobreposicao de um item entre janelas foi observada durante a consulta live.
Ela permanece visivel na evidencia e e tratada pela deduplicacao da camada de
paginação; nao foi convertida em falsa completude.

O detalhe independente continua nao validado. O contrato completo esta no
[dossie do provider](../../providers/tjmt_jurisprudencia_api/README.md).
