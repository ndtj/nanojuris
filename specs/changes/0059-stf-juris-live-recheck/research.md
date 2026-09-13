# Pesquisa - STF Jurisprudencia ciclo 9

O contrato previamente observado aponta para
`https://jurisprudencia.stf.jus.br/api/search/search` com JSON e página pequena.
Nesta rodada a chamada pública bounded falhou durante a verificação TLS padrão,
antes de qualquer resposta HTTP. O provider já expõe `SourceUnavailableError`
para esse estado e nenhuma configuração insegura foi introduzida.
