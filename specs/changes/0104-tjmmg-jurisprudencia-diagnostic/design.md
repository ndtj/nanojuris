# Design — TJMMG bounded

`SharedHttpClient` usa allowlist HTTPS, intervalo mínimo entre requisições,
limite de 2 MB, timeout e nenhum retry. A rota de metadados é parseada somente
para nomes de campos. A busca envia o payload oficial sem campos inventados e
exige número exato ou intervalo fechado de julgamento/publicação, porque a
fonte só pagina no navegador. O envelope `collection` é convertido para
`JurisprudenceResult` e o texto/`NomeArquivo` são preservados. O detalhe PDF é
explícito, validado e convertido para `CanonicalDocument`.

Qualquer limite de transporte, bloqueio, schema desconhecido ou MIME inválido
é propagado como falha explícita; somente `collection: []` de uma consulta
bounded vira vazio autoritativo.

O binding é registrado somente no cliente com
`include_candidate_providers=True`. Isso permite inspeção local e testes sem
inflar a federação ou mascarar a limitação externa.
