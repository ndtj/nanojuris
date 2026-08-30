# Threat model

The CSV and PDF URLs are untrusted public input. The adapter bounds download
size, validates HTTP outcomes, rejects non-official document hosts, and does
not accept credentials or bypass access controls.
