# Design — TSE SJUR jurisprudência textual

O provider usa `SharedHttpClient` com allowlist exclusiva de
`sjur-pesquisa-api.tse.jus.br`, limite de 8 MiB, uma requisição POST não
idempotente por busca e sem retry automático. A API recebe um objeto com
`termoPesquisa` contendo DSL JSON, `pagina`, `tamanho` e `tribunais`.

O analisador traduz apenas texto, expressão exata e número. Filtros de classe,
relator, datas, órgão e tipo permanecem `unsupported` até existir evidência
reproduzível. O filtro de TSE é sempre aplicado no DSL para impedir mistura
com TREs.

O parser converte HTML de ementa/decisão em texto visível, normaliza datas para
ISO e preserva o objeto bruto por registro. Como a fonte ignorou `pagina` e
`tamanho` no smoke público, a resposta é marcada `pagination_mode=none`;
não se promete janela parcial nem iteração de páginas.

Erros de transporte, HTTP 401/403/429, antirrobô e schema são exceções
explícitas. `totalRegistros=0` só é vazio autoritativo quando `mensagem` é nula
e `content` é uma lista vazia.

Quando `temInteiroTeorPDF` é verdadeiro, o parser constrói a rota pública
`sjur-servicos.tse.jus.br/sjur-servicos/rest/download/pdf/<codigoDecisao>`.
O provider guarda apenas URLs associadas a resultados da sessão; downloads
adivinhados ou IDs externos são rejeitados. `DocumentReference` e
`fetch_document_reference` validam host, HTTPS, MIME/magic bytes, hash e limite
de 12 MiB. `get_decisions` retorna o documento baixado sob demanda, sem
persistir o corpo na evidência live.

O provider é anexado ao `NanoJurisClient` padrão como runtime opt-in. Sua
capability mantém `supports_unified_search=False`, portanto a federação padrão
não o roteia enquanto a paginação remota não for comprovada. O registro de
fonte continua separado do provider de catálogo `justica_eleitoral_sjur`,
evitando promoção implícita de TSE/TRE.
