# Design — coleta reprodutível

## Modelo

`CollectionRunManifest` contém run ID, query fingerprint, topology IDs,
provider/capability/parser versions, policy, início/fim, período solicitado,
outcomes, completeness e checkpoints.

`CollectionCheckpoint` v2 contém posição por fonte, página/cursor, último ID,
`run_id`, fingerprint da intenção da consulta, fingerprint do contrato,
tentativas, outcome e hashes estruturais das páginas. A retomada recusa
checkpoints v1 sem fingerprint e qualquer checkpoint de contrato incompatível.
Os contratos JSON estão versionados em
`docs/schemas/collection-checkpoint-v2.schema.json` e
`docs/schemas/collection-manifest-v1.schema.json`.

## Escrita

Cada página é persistida no store antes de avançar o checkpoint; o checkpoint
é escrito com arquivo temporário, `fsync` e replace atômico. A identidade 0037
continua sendo a chave de deduplicação, evitando avançar o cursor sem guardar
dados aceitos.
Queries gravadas em checkpoint/manifesto passam por allowlist mínima e
redaction de identificadores de parte, advogado, OAB e polícia; o fingerprint
continua sendo calculado sobre a intenção original para não perder a validação
de retomada.

## Freshness

Freshness possui pelo menos `observed_at`, `source_updated_at`,
`coverage_end_known` e `evidence_expires_at`. Ausência de data da fonte não é
substituída por `retrieved_at`.

## Tombstone seguro

O SQLite possui um ledger separado `record_tombstones`. A API aceita somente
`TombstoneEvidence` validada com fonte, `canonical_key`, URL HTTPS pública,
SHA-256, tipo de evidência, data de observação e motivo. Os tipos aceitos são
`official_tombstone`, `official_absence_manifest` e `explicit_retraction`.
Registrar evidência não remove nem oculta o registro canônico; a ausência em
uma página de busca nunca gera tombstone por inferência. O schema versionado
está em `docs/schemas/tombstone-evidence-v1.schema.json`.

## Escopo local

O SQLite continua backend inicial. A execução pode ser longa, mas exige limite
de páginas/tempo/bytes configurado e confirmação explícita para expandir o
orçamento.
