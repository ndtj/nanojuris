# Design — 0065

`SearchPage` recebe metadados opcionais no fim do dataclass para preservar
construtores posicionais v1: `total_known`, `access_status` e
`extraction_status`. Providers antigos permanecem válidos; adapters novos
devem preencher os campos quando houver evidência.

O cliente usa `total_known is True` como única autorização para o corte por
total. Uma página vazia só é completa quando o provider informa
`is_complete=True` ou `total_known=True` com total zero. Erros continuam no
envelope de completude.

Os campos canônicos adicionais são opcionais e aditivos. O armazenamento
mantém cópia JSON e materializa colunas/indexes para filtros frequentes; a
migração verifica `PRAGMA table_info` antes de cada `ALTER TABLE`.

Não haverá alteração de catálogo gerado manualmente. Após a implementação, os
geradores serão executados para sincronizar documentação e evidências.
