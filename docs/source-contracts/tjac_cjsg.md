# tjac_cjsg

## Identidade
- Fonte oficial: pesquisa publica de jurisprudencia CJSG/e-SAJ do TJAC.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_esaj_cjsg`.
- URL inicial: `https://esaj.tjac.jus.br/cjsg/consultaCompleta.do`.
- Status de acesso: resultado publico validado em sessao limpa em 2026-08-07.

## Contrato HTTP
- Rotas observadas:
  - `GET /cjsg/consultaCompleta.do`
  - `GET /cjsg/resultadoSimples.do?conversationId=&nuProcOrigem=<numero_cnj>&nuRegistro=`
- Exemplo publico usado no probe:
  - `0700309-51.2015.8.01.0001`
- Metodos: `GET` para formulario e resultado simples por numero.
- Paginacao: reproduzida em sessao publica com `POST /resultadoCompleta.do`
  seguido de `GET /trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>`.
- No fluxo textual CJSG, o POST e um ack de submissao; os registros sao lidos
  nos GETs de `trocaDePagina.do` na mesma sessao.
- Busca textual completa: validada em janela pública bounded; estabilidade
  permanente depende da fonte.

## Dados retornados
- Campos observados:
  - numero CNJ;
  - ementa;
  - relator;
  - orgao julgador;
  - data de julgamento;
  - data de publicacao;
  - link/conteudo de inteiro teor.
- Campos canonicos: `CanonicalDecision`.
- Familia reutilizavel: parser CJSG/e-SAJ deve ser compartilhado com TJSP, TJMS e outros tribunais e-SAJ quando o HTML real permitir.

## Comportamento observado
- Formulario: HTTP 200, CJSG publico.
- Resultado por numero: HTTP 200 com conteudo juridico objetivo.
- Controle de acesso/captcha: observado no detalhe em rechecagem de 2026-09-05;
  a busca continua pública.
- Risco: alto por HTML e-SAJ e possivel controle de acesso dinamico.

## Decisao
- Promover TJAC/CJSG para busca textual federada com a limitação de detalhe
  explicitamente registrada.
- Fixtures sanitizadas e parser compartilhado são suficientes para o contrato
  local; nenhum corpo live é persistido.
- Não usar rotas de captcha ou controle de acesso para bypass.

## MCP e agentes
- Quando usar: demonstracoes de CJSG/e-SAJ com fonte estadual que respondeu em sessao limpa.
- Quando pular: se a fonte retornar captcha, sessao vazia ou login.
- Mensagem segura para o usuario: "A busca usa jurisprudencia publica do TJAC/CJSG e retorna apenas conteudo disponivel sem validacao humana."

## Proximos passos
- [x] Fixture de resultado simples e estados de erro são cobertos pelos
  cenários compartilhados de `provider_contracts.json` e pelos testes do
  adapter.
- [x] Busca por termo em `consultaCompleta` foi reproduzida pelo fluxo
  `resultadoCompleta.do`/`trocaDePagina.do`.
- Inteiro teor permanece condicionado a `getArquivo.do`: a checagem atual
  identificou CAPTCHA/controle de acesso, sem tentativa de bypass.
- Diagnósticos de `tjsp_cjsg` são reutilizados pela família e-SAJ.

## Validacao live de capacidade - 2026-09-05 (ciclo 51)

- Busca pública `responsabilidade civil`, página 1, dois itens: HTTP 200,
  identidade e resumo presentes, total observado `18.299`.
- O detalhe do primeiro registro respondeu com `AccessControlRequiredError`
  (`has_uuid_captcha_field`, `has_recaptcha_widget` e rota de controle).
- A busca é elegível para federação textual; o inteiro teor continua
  explicitamente condicionado ao acesso público da fonte.

Evidência estruturada (sem corpos):
`docs/provider-discovery/cjsg-live-20260905-cycle51.json`.

### Fechamento do contrato local

- `[x]` identidade TJAC/CJSG, resumo, datas e identificador estável;
- `[x]` paginação e sessão pública reproduzidas;
- `[x]` estados de vazio, erro e controle de acesso tipados;
- `[x]` limites, trace e decisão de federação textual registrados.

## Validacao live de capacidade - 2026-08-16

- Consulta: `responsabilidade civil`, duas paginas, 20 itens solicitados.
- Pagina 1: 20 resultados, 20 identificadores unicos, 20 com data.
- Pagina 2: 20 resultados, nenhum identificador repetido, 20 com data.
- Total remoto observado: 18.193.
- Estado: `valid` para a paginacao observada.
- Inteiro teor: continua sob demanda por `getArquivo.do`; a existencia de link
  nao e tratada como documento carregado.

Evidencia estruturada: `docs/validation/runs/20260816T082800Z-cjsg-capacity-20260816.json`.

### Alinhamento Juscraper (2026-09-01, ciclo 12)

O POST de `resultadoCompleta.do` estabelece a sessao; os resultados sao
obtidos por GET de `trocaDePagina.do` para a pagina 1 e a pagina solicitada,
na mesma sessao. Bloqueios permanecem estados explicitos, sem bypass.
