# Threat model

- **Transporte:** a cadeia TLS continua obrigatoria; nenhuma excecao foi adicionada.
- **Proveniencia:** apenas erro e metadados operacionais foram persistidos.
- **Privacidade:** sem cookies, tokens, payload ou dados pessoais.
- **Integridade:** falha TLS nao gera `SearchPage` vazia.
