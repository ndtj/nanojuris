# `trt9_nugepnac_jurisprudencia`

Provider opt-in para as compilações públicas do NUGEP/NUGEPNAC do TRT9. As
rotas oficiais retornam PDFs de precedentes qualificados (por exemplo, IRDR),
que são extraídos em memória e filtrados localmente.

O provider é contextual: não é a busca geral de jurisprudência do TRT9 e não
fecha a cobertura do corpus trabalhista. Cada registro aceito preserva
`authority=TRT9`, `branch=labor`, `degree=second`, `instance=second`, CNJ,
coleção, URL, `raw` e `SourceTrace`. A compilação inteira pode ser recuperada
como documento PDF oficial depois de uma observação na sessão.

PDF inválido, mudança de schema, 403, 429, timeout e erro de transporte são
classificados explicitamente e nunca convertidos em vazio. Não há CAPTCHA,
credenciais ou bypass. Inteiro teor dos votos não é declarado; o material é
ementário/decisões de precedentes qualificados.

Evidência live: `docs/provider-discovery/trt9-nugepnac-live-20260910.json`.
