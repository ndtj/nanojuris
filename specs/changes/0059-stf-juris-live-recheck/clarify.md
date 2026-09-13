# Clarify

- `blocked_transport` é uma falha de conexão TLS, não é `empty` nem
  `blocked_access`.
- O resultado não permite inferir se o endpoint retornaria dados nesta rede.
- Nenhum mecanismo de segurança foi contornado e `verify_ssl=false` não foi
  usado no provider.
