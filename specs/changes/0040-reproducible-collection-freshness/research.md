# Pesquisa — coleta e freshness

## Linha de base

NanoJuris já possui store SQLite, research runs e paginação federada incremental.
O programa anterior não especificava fingerprint de run, compatibilidade de
checkpoint, versionamento de republicações, tombstones ou evidência de período.

## Risco

Sem manifest, duas consultas iguais podem usar contracts diferentes e parecer
reproduzíveis. Sem checkpoint atômico, uma interrupção pode perder ou duplicar
registros. Sem freshness por collection, data de coleta pode ser confundida com
data de atualização do tribunal.
