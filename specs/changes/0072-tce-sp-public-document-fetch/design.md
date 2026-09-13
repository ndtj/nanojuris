# Design

O provider mantém um mapa efêmero `result_id -> document_url`, preenchido por
`search` e `get_catalog`. `get_document` aceita uma URL direta somente quando o
host coincide com `NanoJurisConfig.tce_sp_url`; caso contrário exige um ID
observado. A referência é entregue a `fetch_document_reference` com
`TransportPolicy` restrita ao host oficial e MIME HTML/texto/PDF. O resultado é
um `CanonicalDocument`; `get_decisions` apenas empacota seu texto, sem duplicar
extração ou transporte.

Nenhuma rota dinâmica com CAPTCHA é chamada por esse fluxo.
