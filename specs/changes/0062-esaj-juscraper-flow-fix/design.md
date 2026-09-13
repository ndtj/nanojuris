# Design - Fluxo eSAJ alinhado ao Juscraper

## Fluxo

Cada provider mantém uma `requests.Session` configurada pelo NanoJuris. A
busca CJSG segue:

```text
POST resultadoCompleta.do (formulário)
  -> GET trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=1
  -> GET trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=N (quando solicitado)
  -> parser HTML
```

O primeiro GET é obrigatório mesmo quando a solicitação do usuário é da página
1. A sessão conserva cookies públicos emitidos pelo tribunal. No TJSP, o
`conversationId` presente no HTML da página 1 é incluído apenas nos GETs
posteriores, como no contrato upstream.

## Compatibilidade

`search()` continua retornando `SearchPage`, os identificadores nativos e os
nomes de filtros não mudam. O endpoint registrado no `SourceTrace` passa a ser
o GET que efetivamente forneceu a página interpretada; o payload do POST é
mantido como metadado de consulta já sanitizado pelo provider.

## Segurança e observabilidade

Respostas de controle de acesso continuam lançando `AccessControlRequiredError`.
Falhas de transporte continuam sendo `SourceUnavailableError` ou erro TLS
classificado pelo chamador. Fixtures são sintéticas/sanitizadas e não contêm
corpos capturados de produção.
