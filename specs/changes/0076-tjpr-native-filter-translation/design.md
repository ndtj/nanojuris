# Design - TJPR native filter translation

The TJPR public form uses hidden numeric IDs selected by its public controls.
The adapter receives the IDs through existing string fields in
`JurisprudenceQuery`; it does not scrape or guess labels and does not call any
protected route. A small validator accepts one or more comma-separated decimal
IDs, normalizes whitespace, and rejects other values with `QueryRejectedError`.

`judgment_date_from/to` take precedence over the legacy `updated_from/to`
aliases. The latter remain accepted for compatibility but are documented as
the TJPR judgment-date mapping, not as a source-update timestamp.

No result post-filtering is introduced: the filter is applied remotely by the
official form, preserving source totals and pagination semantics.
