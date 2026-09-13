# TJMA JurisConsult

Status: `runtime_live_validated_catalog` | papel: `catalog_context`

Provider de catalogos publicos do JurisConsult/TJMA. A busca de resultados
jurisprudenciais permanece controlada por captcha e nao e automatizada.

## Identidade E Escopo

- `source_id`: `tjma_jurisconsult`.
- Portal: <https://jurisconsult.tjma.jus.br/>.
- API: <https://apijuris.tjma.jus.br/v1>.
- Escopo implementado: especies de relatorio, tipos de pesquisa, classes,
  magistrados, camaras, comarcas e links de sumulas/precedentes.
- Fora do escopo: coleta automatica de acordaos, decisoes e sentencas.

## Contrato HTTP Observado

Endpoints publicos de catalogo, todos reproduzidos com HTTP 200:

- `GET /jurisprudencia/lista_relatorios`.
- `GET /jurisprudencia/lista_todos_tipos_pesquisa?tipoRelatorio=<id>`.
- `GET /jurisprudencia/lista_todos_classes?tipoRelatorio=<id>`.
- `GET /jurisprudencia/lista_todos_magistrados?tipoRelatorio=<id>`.
- `GET /jurisprudencia/lista_todos_camaras?tipoRelatorio=<id>`.
- `GET /jurisprudencia/lista_todos_comarcas?tipoRelatorio=<id>`.
- `GET /jurisprudencia/links_pesquisa_sumulas`.

As rotas de resultados usam as rotas oficiais `GET /sg/jurisprudencias/processos`
(acórdãos), `/jurisprudencia/processos/pesquisa_acordaos_tr`,
`/jurisprudencia/processos/pesquisa_monocraticas` e
`/jurisprudencia/processos/pesquisa_monocraticas_tr`. Todas exigem `tokenG` e
`keyId` de captcha. O provider declara essas rotas para manter o contrato
observável, mas retorna
`AccessControlRequiredError` sem tentar criar ou reutilizar desafio.

Quando uma resposta autorizada inclui `arquivosAcordao` com
`bol_permite_consulta_publica`, `strArquivo` e `strTipoDocumento`, o parser
preserva o inteiro teor (`txAcordao`/campos equivalentes) e constrói apenas a
referência oficial `GET /sg/download_acordao_pauta_julgamento?filename=...`.
Isso não faz download automático nem remove a exigência do desafio.

## Dados Retornados

`ProviderCatalog.species` recebe os relatorios oficiais. O payload bruto
preserva classes, magistrados, camaras, comarcas, tipos de pesquisa e links de
IRDR/IAC/sumulas em `catalog.raw`.

## Filtros E Paginaçao

O catalogo aceita o identificador `tipoRelatorio` nas rotas oficiais. Nao ha
paginaçao de resultados implementada porque a busca principal esta gated.

## Inteiro Teor E Documentos

Nao aplicavel nesta superficie para coleta automatica. A rota de resultados e
protegida por CAPTCHA e nao foi observada uma rota publica automatizavel de
inteiro teor (`full_text_access=access_blocked`). O caminho de documento so e
exposto em resultado autorizado que declare permissao publica; nenhum link de
catalogo e promovido como documento carregado.

## Estados E Falhas

- Catalogos publicos: `access_status=public`.
- Busca principal: `access_control_required` por captcha.
- Falha de rede ou 5xx: `SourceUnavailableError`.
- HTTP 429: `RateLimitDetectedError`.

Captcha nao e convertido em vazio nem em provider textual funcional.

## Evidencias, Fixtures E Testes

- Fixture: `tests/fixtures/tjma_jurisconsult_catalog.json`.
- Testes: `tests/test_tjma_jurisconsult.py`.
- Evidencia live do catalogo: `docs/validation/runs/20260816T125603Z-tjto-tjma-tjro-live.json`.
- Evidencia live da fronteira de acesso: `docs/provider-discovery/tjma-jurisprudencia-captcha-live-20260906.json`.
- Rodada: 7 especies, 135 classes e 313 magistrados observados.

## Implementaçao E Integraçao

- Modulo: `src/nanojuris/providers/tjma_jurisconsult.py`.
- Classe: `TjmaJurisconsultProvider`.
- Interfaces: catalogo Python, CLI, Studio e MCP; fora da busca unificada.

## Transporte compartilhado (2026-09-08)

Os endpoints pÃºblicos de catÃ¡logo agora usam `SharedHttpClient`, com allowlist
TJMA, limite de 4 MB, timeout, rate limit e circuito. A busca de resultados
continua explicitamente protegida por CAPTCHA; 400 de desafio, 401/403, 429,
TLS, timeout, schema e JSON invÃ¡lido nÃ£o sÃ£o convertidos em catÃ¡logo vazio.

## MCP E Agentes

O agente pode usar o catalogo para desenho amostral e descoberta de filtros,
mas deve dizer que ele nao contem resultados coletados. A busca textual deve
ser reportada como controlada por captcha.

## Promocao

O provider esta no maximo comprovado para catalogo publico. So pode ganhar
busca textual quando existir uma superficie oficial sem captcha ou um fluxo
interativo explicitamente operado pelo usuario.

### Rechecagem legítima (2026-09-06)

A API oficial `apijuris.tjma.jus.br/v1` respondeu aos catálogos de relatórios,
tipos e classes. A rota de acórdãos, porém, exige token CAPTCHA server-side;
sem esse token a fonte não entrega resultados decisórios. O estado continua
`access_controlled`, sem geração ou reutilização de tokens.

## Proximos Passos

- monitorar a disponibilidade dos catalogos publicos;
- registrar mudancas de vocabulário e relatorios;
- nao automatizar a busca enquanto o captcha continuar sendo requisito;
- investigar somente superficies oficiais alternativas sem desafio.

### Rechecagem de alternativas oficiais (2026-09-07)

Foram consultados o shell oficial JurisConsult, o catálogo da API, o portal
institucional, `robots.txt` e os caminhos convencionais de OpenAPI. Os
catálogos responderam publicamente, mas as rotas de resultados continuam
exigindo `tokenG`/`keyId` de CAPTCHA. Nenhuma tentativa de gerar, reutilizar ou
contornar desafio foi feita. Evidência: `docs/provider-discovery/tjma-official-alternatives-live-20260907.json`.

### Rechecagem bounded das rotas decisórias (2026-09-08)

As rotas oficiais de acórdãos, decisões monocráticas e sentenças foram
consultadas sem credenciais e com requisição mínima. Todas responderam
`400 {"error":"captcha_not_provided"}`. O resultado é um bloqueio de acesso
explícito, não uma busca vazia; nenhum token foi criado, reutilizado ou
contornado. A evidência redigida está em
`docs/provider-discovery/tjma-jurisprudence-route-live-20260908.json`.

As superfícies CJSG e CJPG permanecem fora da federação até que exista uma
rota oficial pública sem o desafio ou um fluxo autorizado operado pelo usuário.

### Evidência de bloqueio das rotas de resultados (2026-09-08)

As rotas oficiais `/sg/jurisprudencias/processos`,
`/jurisprudencia/processos/pesquisa_acordaos_tr`,
`/jurisprudencia/processos/pesquisa_monocraticas`,
`/jurisprudencia/processos/sentencas_pg` e
`/jurisprudencia/processos/sentencas_je` responderam `400` com
`captcha_not_provided` em chamadas públicas bounded. Os catálogos continuam
com `200`. A classificação é `access_blocked`, nunca `authoritative_empty`.

Evidência: `docs/provider-discovery/tjma-jurisprudence-route-live-20260908.json`.

### Contrato observado no frontend oficial (2026-09-11)

O shell oficial e os chunks públicos `build/main.js`, `build/5.js` e
`build/197.js` confirmam o contrato de segundo grau: `GET` na rota do relatório,
paginação por `inicioPagina`/`fimPagina`, filtros `chave`, `tipoPesquisa`,
`relator`, `camara`, `classe`, `dtaInicio`, `dtaFim`, `checkForm` e
`fraseExata`. A chamada também exige um bearer transitório, `tokenG` e `keyId`
gerados pela interação do usuário com o desafio oficial.

O método `search_authorized` implementa essa rota sem gerar, resolver,
armazenar ou reutilizar tokens. Ele é deliberadamente não federado: recebe os
três valores apenas em memória para uma única página, não os inclui no
`SourceTrace` e desativa o cache de transporte. Sem esses valores, `search`
continua retornando `AccessControlRequiredError`. A evidência dos chunks e dos
campos observados está em
`docs/provider-discovery/tjma-jurisconsult-frontend-contract-live-20260910.json`.
