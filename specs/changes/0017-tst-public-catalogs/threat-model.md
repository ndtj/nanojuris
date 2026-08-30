# Threat model

The method performs public read-only GET requests. It does not accept or store
credentials. Response data is treated as untrusted JSON; only bounded strings
with explicit source keys become options. Network failures and schema changes
remain visible to callers and are not converted into zero results.
