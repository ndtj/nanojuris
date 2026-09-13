# Design - Rechecagem bounded do STF Informativo

O ciclo faz duas tentativas controladas na mesma rota oficial: primeiro com a
verificacao TLS padrao e, somente para diagnostico local, uma segunda tentativa
com `verify_ssl=False`. O artefato guarda status, erro, tamanho e hash do HTML
de erro, mas nao guarda o corpo. A decisao de produto continua inalterada:
`blocked_transport` e `blocked_access` sao estados operacionais e nao uma
resposta de busca vazia.
