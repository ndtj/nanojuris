# Design

The provider uses one bounded GET for an explicitly selected annual CSV,
decodes UTF-8/CP1252/Latin-1, parses `;`, filters rows locally, and returns
`JurisprudenceResult` with a `SourceTrace` hash and byte count. It preserves
the complete row in `raw`, but accepts document URLs only on the official
ViaJuris host. Catalog construction is metadata-only.
