# Design

The fixture is a minimal, synthetic representation of the public TJPA BFF
search envelope. The test loads it from `tests/fixtures` and calls
`parse_tjpa_search_response` directly. This protects the normalized model
without coupling tests to network availability or mutable court records.

No new runtime route is introduced and no unverified detail endpoint is
promoted.
