# Design

`TstJurisprudenciaProvider.get_catalog()` iterates the route list already
declared in the provider capability contract. Each route is fetched with the
provider's existing safe request path, then normalized by `_catalog_options`.

The normalizer accepts explicit identifiers (`id`, `codigo`, `cod`, `value`)
and labels (`descricao`, `description`, `nome`, `name`, `label`). Strings are
accepted only when the value itself is both code and description. Unknown
objects are ignored rather than guessed. The complete source envelopes remain
in `raw`; normalized groups are exposed in `species_groups`, while process
classes populate the legacy `species` field.

No credentials, cookies, access-control workarounds, or production settings
are introduced.
