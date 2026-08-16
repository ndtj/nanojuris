# TJTO — revalidacao anonima do portal

- Data: 2026-08-16 17:35 UTC.
- URL: <https://jurisprudencia.tjto.jus.br/>.
- Modo: navegador headless sem login, cookies pessoais ou credenciais.
- Resultado: HTTP 403 antes de renderizar o formulario.
- Requisicao de pesquisa observada: nao.
- Decisao: manter `tjto_jurisprudencia` como candidato dependente de HAR
  anonimo; nao inventar payload, paginacao ou detalhe.

Essa evidencia nao invalida uma observacao manual diferente, mas mostra que a
rota nao foi reproduzida neste ambiente. O provider somente deve ser criado
quando o HAR puder ser reduzido a uma chamada publica reproduzivel sem
credenciais ou contorno de controle de acesso.
