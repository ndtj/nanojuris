# Design - Rechecagem live STF Jurisprudencia

O artefato usa o envelope `results` para integração com o gerador de cobertura
e mantém uma lista `attempts` com a política TLS observada. Como a conexão
falhou antes de HTTP, `response_bytes` e `content_sha256` permanecem nulos/zero
e `record_count_observed` é apenas um marcador de ausência de observação, não
um total de jurisprudência.
