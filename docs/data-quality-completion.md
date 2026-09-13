# Fechamento de qualidade de dados

Este documento descreve as garantias aditivas implementadas no ciclo 0065.

## Total e acesso

`SearchPage.total_known` só é `True` quando o adapter comprovou o total remoto.
O valor histórico `total=0` sem esse marcador é tratado como desconhecido. A
federação só encerra por contagem quando o marcador é explícito; páginas vazias
continuam distintas de bloqueios, timeouts e mudanças de schema por meio de
`access_status`, `extraction_status` e `access_reason`.

## Dimensões canônicas

Consulta, resultado e registros canônicos aceitam `case_class`, `judging_body`,
`degree`, `instance`, `branch`, `legal_area`, `authority`, `collection`,
`document_type` e `source_origin`. Os valores são opcionais: ausência não é
inferida e o valor original permanece em `raw`.

## Armazenamento

O SQLite migra bancos existentes de forma idempotente e indexa as dimensões,
datas de julgamento/atualização, URL de documento e estado de acesso. O JSON
canônico permanece a fonte de auditoria; os índices são apenas projeções para
consultas eficientes.

## Limites

O ciclo não promove candidatos nem contorna controles dos tribunais. A
disponibilidade de cada fonte ainda exige chamada live limitada, fixture
sanitizada, contrato oficial e aprovação de governança.
