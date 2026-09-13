# Design

O adapter usa `requests.Session` configurada pela política compartilhada. A
primeira requisição GET carrega campos do formulário; o POST retorna edições e
seções. Uma única entrada de seção é selecionada por página e o POST de
`principal.wsp` carrega a lista textual da edição. O servidor usa páginas de
1000 linhas; o adapter fatia no limite NanoJuris (100) e informa que o total
global entre edições não é conhecido.

Linhas de seção sem links de processo/acórdão são cabeçalhos de classe e não
viram registros. Cada registro mantém a ementa integral disponível no HTML,
identificadores nativos e links oficiais. O detalhe é servido a partir do
conteúdo obtido na busca; não há tentativa de contornar qualquer desafio.
