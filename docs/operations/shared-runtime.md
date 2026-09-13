# Runtime compartilhado de providers

O módulo `nanojuris.transport` é a fronteira comum para adapters que usam
HTTP público. Ele não conhece parsers nem promove providers automaticamente.

## Política

Cada adapter cria `TransportPolicy` com hosts oficiais allowlisted, HTTPS
obrigatório, timeout, limite de bytes, limite de redirects, intervalo por host
e número máximo de retries. `TransportRequest.idempotent` deve ser `False` para
POST que não tenha contrato seguro de repetição.

## Estados

`TransportResponse.status` distingue `complete`, `timeout`, `tls_error`,
`source_unavailable`, `redirect_limit`, `redirect_outside_allowlist`,
`response_too_large` e `circuit_open`. Um status de transporte nunca é
convertido em lista vazia pelo parser.

## Cache e circuit breaker

`ContentResponseCache` é opcional e grava envelopes atômicos por hash da
requisição. `CircuitBreaker` é isolado por `(source, operation)`. Para inteiro
teor, `DocumentReference` exige URL HTTPS e `fetch_document_reference` só é
chamado explicitamente; `ContentAddressedDocumentCache` grava bytes por
SHA-256 e um sidecar de metadados.

## Logs e evidência

Use `redact_url`, `redact_headers` e `redact_payload` antes de persistir
diagnósticos. Nunca registre cookies, tokens, corpo jurídico completo ou
credenciais. A suíte padrão é offline; probes live utilizam
`nanojuris.observability.ProbePolicy` com allowlist explícita e orçamento
limitado.

## Providers migrados nesta rodada

TJES/CJSG, TJTO/Jurisprudência e TJRN usam a camada compartilhada. A migração
é incremental: os demais adapters continuam compatíveis com a API anterior e
devem migrar somente quando seus contratos e fixtures forem revisados.
