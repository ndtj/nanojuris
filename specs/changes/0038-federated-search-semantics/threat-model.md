# Threat model — busca federada

| Ameaça | Impacto | Controle |
| --- | --- | --- |
| ranking enganoso | alto | scores namespaced e ordenação comparável |
| filtro omitido sem aviso | alto | query plan e completeness |
| cursor reutilizado após drift | médio | fingerprint versionado |
| fonte falha mascarada | alto | outcome por fonte |
| query/PII em trace | alto | redaction estrutural |
