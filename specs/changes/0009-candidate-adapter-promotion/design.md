# Design

`JusticaEleitoralSjurProvider` uses the public SJUR API host configured in
`NanoJurisConfig`. `get_catalog()` calls the four reproduced metadata routes
with the public tribunal payload and normalizes heterogeneous JSON items into
`ProviderOption` while preserving each raw item.

The adapter is catalog-only. `search()` and `get_decisions()` fail closed with
`UnsupportedQueryError`; they do not submit speculative search payloads.
