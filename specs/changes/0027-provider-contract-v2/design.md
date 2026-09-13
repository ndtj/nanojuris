# Design — contrato de provider v2

## Componentes

- ProviderIdentity: source_id, tribunal, autoridade e categoria.
- ProviderCapabilities: operações e semântica declarada.
- QuerySupport: suporte por filtro e limitações.
- PaginationContract: page, offset, cursor, unknown e limites.
- ProviderOutcome: valid, empty, invalid_query, blocked, rate_limited, timeout,
  unavailable, tls_error e parser_changed.
- SourceTrace e ExtractionTrace: origem e transformação.
- CompatibilityAdapter: converte v2 para os modelos públicos atuais.

## Compatibilidade

O v2 começa interno. Adapters podem implementar capability v2 sem alterar
assinaturas públicas. A remoção de campo ou mudança de tipo exige versão major.

## Invariantes

- unknown não equivale a false ou zero;
- raw não pode conter segredo;
- identity precisa ser determinística;
- erro é dado por fonte, não exceção genérica federada;
- paginação não pode declarar complete sem prova.
