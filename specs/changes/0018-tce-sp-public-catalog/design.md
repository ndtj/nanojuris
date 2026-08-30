# Design

`TceSpJurisprudenciaProvider.get_catalog()` reuses the existing safe GET
transport and parsers for the public sumula and bulletin pages. It maps the
two known collection types to `ProviderOption`, reports counts in
`species_groups`, and preserves each parsed record in `ProviderCatalog.raw`.
The dynamic CAPTCHA route is not called.
