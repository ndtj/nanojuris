# Traceability

| Requirement | Implementation | Evidence |
| --- | --- | --- |
| REQ-001 | `TstJurisprudenciaProvider.get_catalog` route tuple | `test_tst_catalog_routes_are_normalized_and_raw_payloads_preserved` |
| REQ-002 | `_catalog_options` explicit keys only | same test |
| REQ-003 | `ProviderCatalog.raw` and `SourceTrace` | same test |
| REQ-004 | additive provider method | full provider test module |
