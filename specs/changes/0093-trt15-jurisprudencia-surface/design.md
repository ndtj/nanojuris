# Design — TRT15

O provider usa o transporte HTTP comum e uma allowlist estrita para
`jurisprudencia.trt15.jus.br`. `GET /backend/listarOpcoes` é seguro para
descoberta. `POST /backend/pesquisar` envia filtros oficiais e campos de
desafio vazios somente para observar o contrato; `sucesso=3` encerra com
`AccessControlRequiredError`.

Resultados autorizados, caso a fonte ofereça esse acesso no futuro, usam os
campos declarados pela SPA: `id`, processo, classe, ementa, data, órgão,
relator e link. O grau é `unknown` até aparecer um campo ou escopo oficial que
o comprove. O detalhe usa `POST /backend/visualizarDocumento` com o
`idPesquisa` da mesma sessão.

O provider é runtime, catalogável, MCP/CLI/Studio-compatible e não é fonte da
federação padrão. Nenhum token ou corpo de desafio é persistido.
