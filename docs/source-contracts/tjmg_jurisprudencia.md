# TJMG - Espelho De Acordao

Status atual: `live_validated` para a API pública CJSG; o formulário legado
continua `blocked_control` por CAPTCHA.

## Identidade Da Fonte

- Tribunal: Tribunal de Justica do Estado de Minas Gerais.
- Formulario oficial: `https://www5.tjmg.jus.br/jurisprudencia/formEspelhoAcordao.do`.
- Busca por numero: `/jurisprudencia/pesquisaNumeroCNJEspelhoAcordao.do`.
- Busca por palavras: `/jurisprudencia/pesquisaPalavrasEspelhoAcordao.do`.

## Contrato Observado

A ajuda oficial documenta pesquisa de espelho de acordao, consulta por numero
CNJ, consulta textual e acesso ao inteiro teor. O formulario apresenta campos
juridicos suficientes para uma futura ficha de provider.

## Diagnostico De Acesso

A busca textual testada com termo juridico retornou HTTP 401 e pagina de
captcha. O NanoJuris nao deve automatizar ou contornar essa etapa. A ajuda e o
formulario comprovam a existencia da fonte, mas nao comprovam contrato live
reproduzivel.

Classificacao: `blocked_control`, evidencia `B`.

## Promocao Futura

Somente promover com uma superficie oficial que retorne resultado sem captcha
ou com fixture obtida de fluxo publico permitido. Nao versionar tokens,
cookies, credenciais ou dados de desafio.

## Validacao live 2026-08-16

- O portal institucional respondeu HTTP 200 e redirecionou para o portal RUPE.
- A pagina publica exibiu um link para o formulario legado de espelho de
  acordao em `www5.tjmg.jus.br`.
- A superficie atual nao comprovou busca textual reproduzivel; a evidencia
  anterior de HTTP 401/captcha permanece aplicavel ao formulario legado.
- Nao houve tentativa de contorno.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Fontes Oficiais

- [Formulario de espelho de acordao](https://www5.tjmg.jus.br/jurisprudencia/formEspelhoAcordao.do)
- [Ajuda da pesquisa](https://www5.tjmg.jus.br/jurisprudencia/ajuda.do)
## Dados E Filtros

A fonte possui duas superficies distintas: pesquisa por numero CNJ e pesquisa por palavras/espelho de acordao. A ajuda/formulario indicam campos de numero, palavras, classe, orgao, relator, periodo e acesso ao inteiro teor, mas os names, payloads, paginacao e schema de resultado nao foram reproduzidos. A resposta 401/captcha nao deve ser usada para inferir campos retornados.

## MCP

O MCP pode usar a API moderna pública CJSG quando a chamada bounded estiver
disponível. O formulário legado `www5` continua `blocked_control` e não pode
ser submetido para resolver CAPTCHA ou reaproveitar tokens; falhas dessa rota
devem permanecer separadas do estado da API moderna.

### Rechecagem CJPG 2026-09-09

A rota oficial `pesquisaPalavraSentenca.do` respondeu HTTP 401 com pagina de
codigo/CAPTCHA para uma consulta bounded. O estado continua `access_blocked`;
nao ha adapter CJPG promovido. Evidencia:
`docs/provider-discovery/tjmg-cjpg-legacy-live-20260909.json`.

## Diagnostico NanoJuris 2026-09-06

O adapter independente `tjmg_jurisprudencia` agora reproduz a descoberta do
formulário do Juscraper (`GET /jurisprudencia/formEspelhoAcordao.do`) em modo
opt-in. A presença de `txtcaptcha`/reCAPTCHA é classificada como
`access_controlled`; o adapter não envia solução, não faz OCR e não transforma
o bloqueio em lista vazia. A evidência bounded está em
`docs/provider-discovery/juscraper-captcha-boundary-live-20260906.json`.
Fixture sanitizada do formulário: `tests/fixtures/tjmg_jurisprudencia_captcha.html`.

### Rechecagem da superfície de sentenças (2026-09-07)

Além do espelho de acórdãos, o portal oficial expõe
`GET /jurisprudencia/sentenca.do`, com filtros de primeiro grau. A submissão
normal de `pesquisaPalavraSentenca.do` para `dano moral` respondeu HTTP 401 com
a página oficial de CAPTCHA numérico. Não houve solução, OCR ou reaproveitamento
de sessão. Evidência: `docs/provider-discovery/tjmg-cjpg-route-live-20260907.json`.
O resultado mantém TJMG/CJPG como `access_controlled`, sem falso vazio.
## API pública moderna (2026-09-07)

O portal oficial `consulta-jurisprudencia.tjmg.jus.br` publica o backend
`https://jurisprudencia-api.tjmg.jus.br`. O adapter usa `POST
/jurisprudencias/filter` para CJSG, com paginação zero-based convertida para o
contrato NanoJuris, filtros nativos de número, classe, órgão julgador,
magistrado, comarca e datas, e `tipoTexto=EMENTA` ou `INTEIRO_TEOR`. O inteiro
teor é recuperado sob demanda em `POST /jurisprudencias/document` com
`documentoId` e data de publicação ISO. O formulário `www5` com CAPTCHA não é
submetido nem contornado.

Evidência bounded: `docs/provider-discovery/tjmg-modern-api-live-20260907.json`.
Fixtures sanitizadas: `tests/fixtures/tjmg_jurisprudencia_modern.json`,
`tests/fixtures/tjmg_jurisprudencia_modern_empty.json`,
`tests/fixtures/tjmg_jurisprudencia_modern_error.json` e
`tests/fixtures/tjmg_jurisprudencia_modern_schema.json`.

### Rechecagem live bounded 2026-09-11

Uma consulta pública limitada (`divorcio`, página 1, tamanho 1) retornou
HTTP 200 em `/jurisprudencias/filter`, um registro e total autoritativo 1000.
O detalhe público em `/jurisprudencias/document` também retornou HTTP 200 e
8.434 caracteres de inteiro teor. Nenhum token, cookie ou texto bruto foi
persistido. Evidência sanitizada:
`docs/provider-discovery/tjmg-modern-api-live-recheck-20260911.json`.

### Rechecagem de documento live bounded 2026-09-13

Nova sessão pública limitada confirmou novamente HTTP 200 na busca CJSG e no
detalhe de inteiro teor. O detalhe retornou 4.431 caracteres e 8.584 bytes;
hash, MIME, tamanho e `access_status=public` foram preservados somente como
metadados. Nenhum corpo foi persistido. Evidência:
`docs/provider-discovery/tjmg-modern-api-document-live-20260913.json`.

## Capability alignment (2026-09-12)

The modern API-backed adapter now declares the filters it already sends:
`types`, `document_type`, `decision_type`, `courts` and `legal_area` are native;
`exact_phrase` and `all_words` are translated through the free-text channel.
`any_words` and `without_words` are rejected because their independent remote
semantics are not proven. Type aliases are de-duplicated before transport.
