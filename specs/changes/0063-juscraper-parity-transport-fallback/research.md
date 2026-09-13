# Pesquisa - rotas públicas observadas

- Juscraper documenta o TJPE como aplicação JSF/RichFaces: GET de `consulta.xhtml`
  para ViewState, POST de consulta, possível escolha em `escolhaResultado.xhtml`
  e POST AJAX em `resultado.xhtml` para paginação.
- O mesmo projeto monta no TJCE um adaptador SSL com `SECLEVEL=1`, mantendo
  `requests` e validação de certificados.
- A camada HTTP do Juscraper aplica retry bounded para 403, 429 e 5xx, com
  backoff; isso não resolve CAPTCHA e não é um bypass de acesso.
- A rota TJTO observada é `POST /consulta.php` e a página de ementa é
  `GET /ementa.php?id=<uuid>`; o NanoJuris preserva sua rota documentada
  `documento.php` até existir prova de compatibilidade sem quebra.

Fonte primária auditada: https://github.com/jtrecenti/juscraper (MIT), arquivos
`src/juscraper/courts/tjpe/download.py`, `tjpe/parse.py`, `tjce/_tls.py` e
`core/http.py`.
