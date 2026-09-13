# Design

Durante `search`, o provider mantém um mapa efêmero de `result_id` para
`cnot_url`. `get_document` aceita uma URL explícita apenas no host configurado
ou um ID presente nesse mapa. O corpo passa por `fetch_document_reference` e é
normalizado como `CanonicalDocument`; `get_decisions` apenas converte esse
documento em `DecisionBundle`. O link `acordao_url` continua preservado em
`raw`, mas não é usado como fallback porque pode exigir controle de acesso.
