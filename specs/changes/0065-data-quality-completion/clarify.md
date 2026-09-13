# Perguntas e decisões — 0065

- Total remoto ausente continua compatível como inteiro legado, mas recebe
  `total_known=None`; adapters usam `True` somente com evidência explícita.
- Campos semânticos não são inferidos de texto quando a fonte não os declara;
  permanecem `None` e o valor original fica em `raw`.
- Datas de julgamento, publicação e atualização mantêm valor original e forma
  ISO normalizada para ordenação e filtros.
- A entrega é local e não inclui publicação, push ou alteração em produção.
