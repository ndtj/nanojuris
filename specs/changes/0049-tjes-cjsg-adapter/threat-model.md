# Modelo de ameaças

- **Falsa cobertura:** core fixo em `pje2g`; nenhum provider misto é promovido.
- **Schema drift:** raiz, core, paginação, identidade e tipos são validados.
- **Dados pessoais:** fixtures sem conteúdo real; logs carregam metadados e
  hash, não o corpus.
- **Abuso da fonte:** timeout, limite de 20 e intervalo configurável; sem
  coleta massiva ou bypass.
- **Acesso:** 401/403 e controles do portal são outcomes explícitos.
- **Reuso:** adapter permanece opt-in até revisão de termos e redistribuição.
