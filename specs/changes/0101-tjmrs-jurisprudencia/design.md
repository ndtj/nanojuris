# Design — TJMRS por processo exato

## Transporte

`SharedHttpClient` usa a allowlist HTTPS `www.tjmrs.jus.br`, timeout e limite
de 8 MB, retry idempotente controlado, rate limit e circuito compartilhados.
Não há fallback para host alternativo.

## Parsing

O parser remove scripts e estilos, extrai texto visível e procura:

1. número CNJ formatado;
2. identificador `Documento` quando publicado;
3. classe/tipo anterior ao número;
4. relator;
5. seção `EMENTA`;
6. marcadores de ausência de acórdão.

A presença de um aviso de ausência junto com ementa e relator não invalida a
decisão: o portal pode exibir o aviso para componentes não publicados da peça.
Uma página sem decisão e sem marcador autoritativo gera
`ParserContractChangedError`.

## Contrato de consulta

O adapter usa `GET /abreJurisprudencia.php?processo=<20 dígitos>`, uma janela
única por processo. O resultado expõe `JurisprudenceResult`; `get_document`
constrói `CanonicalDocument` a partir dos mesmos bytes HTML. Não há chamada
automática adicional nem pesquisa no cache.

## Promoção

A implementação é runtime opt-in e `supports_unified_search=false`. A fonte
só poderá ser reavaliada para federação se o TJMRS publicar um contrato geral
com filtros, paginação e total verificáveis.
