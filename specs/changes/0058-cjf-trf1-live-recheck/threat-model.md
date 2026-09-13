# Threat model

- **Acesso:** nenhum mecanismo de desafio foi contornado.
- **Proveniencia:** somente hash, tamanho e marcadores foram persistidos.
- **Privacidade:** nao foram salvos cookies, ViewState, tokens ou dados pessoais.
- **Integridade:** o teste exige `runtime_unchanged` e bloqueio distinto de vazio.
