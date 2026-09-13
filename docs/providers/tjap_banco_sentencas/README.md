# TJAP Banco de Sentenças

## Identidade

Provider `tjap_banco_sentencas` para a coleção pública oficial de decisões e
sentenças de primeiro grau do TJAP.

- Entrada: <https://bancosentencas.tjap.jus.br/>
- Transporte: GET do snapshot Livewire e POST `livewire-53cc04b2/update` com o
  evento público `update-filters`; paginação por `gotoPage`.
- Identidade: unidade judicial de primeiro grau (vara, juizado, comarca ou
  ofício), processo CNJ e ID numérico do leitor.
- Texto: teor público inline e leitor oficial `/reader/TUCUJURIS/<id>`; registros
  sigilosos permanecem parciais.
- Escopo canônico: `authority=TJAP`, `branch=state`, `degree=first`,
  `instance=first`, `collection=CJPG`.

## Contrato

A fonte está habilitada na busca federada como superfície CJPG de primeiro grau,
com o limite explícito de ser uma coleção curada. Não é a mesma superfície que
`tjap_tucujuris`: o CJSG Tucujuris continua bloqueado por Turnstile/WAF e não é
contornado.

## Dados

Os campos `case_number`, `case_class`, `judging_body`, `rapporteur`,
`judgment_date`, `summary`, `full_text` e `document_url` são preservados no
resultado canônico e em `raw`.

## Estados

HTTP 403/429, timeout e schema drift permanecem estados explícitos; processos
sigilosos usam `extraction_status=partial` quando a fonte não publica o teor.

## Fixtures

Parser coberto por `tests/fixtures/tjap_banco_sentencas_success.html`,
`tests/fixtures/tjap_banco_sentencas_empty.html`,
`tests/fixtures/tjap_banco_sentencas_sigiloso.html` e
`tests/fixtures/tjap_banco_sentencas_blocked.html`.

## Transporte compartilhado (2026-09-08)

O protocolo Livewire agora usa `SharedHttpClient` com allowlist do host oficial,
limite de 8 MB, timeout, rate limit e circuito. GET inicial, dispatch POST,
paginação e leitor passam pelo mesmo transporte; 403/429, desafios, timeout,
TLS, redirecionamentos e schema inválido permanecem distintos de vazio.

## MCP

O provider declara suporte MCP/Studio, com a mesma semântica de estados e
limitação de escopo de primeiro grau.

## Rechecagem live bounded - 2026-09-13

A busca pública por `direito` retornou um registro de primeiro grau (HTTP
200), e o leitor oficial entregou 7.368 caracteres em HTML público. Hashes,
tamanhos e estados foram preservados sem corpo em
`docs/provider-discovery/tjap-banco-sentencas-live-20260913.json`.

## Próximos passos

Validar estabilidade em smokes periódicos. A rota CJSG Tucujuris continua
bloqueada.

Evidência bounded: [tjap-banco-sentencas-live-20260907.json](../../provider-discovery/tjap-banco-sentencas-live-20260907.json).
