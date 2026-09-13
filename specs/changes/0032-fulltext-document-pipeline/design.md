# Design — inteiro teor

## Fluxo

    SearchResult
      -> DocumentReference
      -> explicit fetch
      -> size/content-type gate
      -> immutable bytes + SHA-256
      -> format parser
      -> CanonicalDocument
      -> link to CanonicalDecision

## Controles

- allowlist por provider;
- limite antes e durante download;
- redirects validados;
- arquivo temporário imprevisível quando inevitável;
- nenhum conteúdo executado;
- OCR isolado;
- cache content-addressed;
- quarentena e exclusão segura definidas.
