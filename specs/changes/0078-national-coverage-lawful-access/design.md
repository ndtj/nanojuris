# Design — cobertura nacional

## Fluxo

```text
catálogo oficial -> CoverageSurface -> discovery bounded
-> AccessEvidence -> capability ledger -> adapter/parser/document fetcher
-> fixtures e testes diferenciais -> CanonicalDecision/Document
-> federação e promoção local
```

## Estados

```text
cataloged -> contract_pending -> fixture_pending -> live_validated
          -> quality_passed -> federation_enabled
```

Dimensões paralelas:

```text
access: public | challenge_incidental | challenge_enforced | blocked | unavailable
document: inline | detail | download | ocr | not_offered | blocked | unknown
```

`CoverageSurface` é a chave nacional. `ProviderBinding` liga superfície a
provider. `AccessEvidence` guarda data, rota, método, status, fingerprint,
classificação, latência e trace redigido. `CapabilityLedger` guarda filtros,
campos, paginação, ordenação, detalhe, documentos e falhas.

Famílias eSAJ, eproc, PJe, Projudi, GraphQL/BFF, JSF e Solr compartilham
transporte, mas cada tribunal mantém overlay de URL, payload, enumeração,
seletores, grau, erro, fixture e evidência.

## Documentos

```text
SearchResult -> DocumentReference -> fetch allowlisted
-> redirect/MIME/magic-bytes/size -> SHA-256
-> HTML/PDF/text/OCR isolado -> CanonicalDocument
```

Busca não baixa corpus em massa; inteiro teor é fetch explícito e limitado.

