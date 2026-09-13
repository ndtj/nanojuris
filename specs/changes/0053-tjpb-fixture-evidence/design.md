# Design - Fixture de replay TJPB/PJe

A fixture JSON representa somente o envelope que o parser consome depois da
decodificacao HTTP. Ela e deliberadamente pequena, com identificador e textos
marcados como `fixture`, para impedir que um replay local seja confundido com
acervo real. O teste continua usando `parse_tjpb_search_response`, preservando
as regras de pagina, limite de dez itens, limpeza da ementa e construcao das
URLs de detalhe.

Nenhum campo de autenticacao e copiado. O token CSRF permanece obtido em tempo
de execucao e nunca e versionado. A fixture nao muda registro, disponibilidade,
status ou federacao do provider.
