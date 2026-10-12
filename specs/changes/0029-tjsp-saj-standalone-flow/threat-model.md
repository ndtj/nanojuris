# Threat model

| Asset | Threat | Mitigation |
| --- | --- | --- |
| Source access | CAPTCHA/control bypass | control route is never called |
| Session privacy | persisted cookies or tokens | one in-memory session only |
| Search truth | control form treated as empty | explicit access state |
| Target integrity | posting to a changed host | form action host allowlist |
| Source load | repeated or mass requests | one bounded query and source rate limit |
