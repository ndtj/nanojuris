# `tjam_cjsg`

## Identidade

- Fonte oficial: Consulta de Jurisprudencia CJSG/e-SAJ do TJAM.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_esaj_cjsg`.
- URL inicial: `https://consultasaj.tjam.jus.br/cjsg`.
- Status de acesso: publico, sujeito a indisponibilidade ou controle da fonte.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `POST /resultadoCompleta.do`
  - `GET /getArquivo.do?cdAcordao=<id>&cdForo=<foro>`
- Metodos: `POST` para busca e `GET` para arquivo publico.
- Parametros: texto integral, ementa/resumo, numero CNJ, intervalo de data e
  tipo decisorio.
- Paginacao: reproduzida em sessao publica com `POST /resultadoCompleta.do`
  seguido de `GET /trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>`.
- O POST inicial somente estabelece a sessao; os resultados vem de
  `trocaDePagina.do`.
- Limite remoto observado: 10 resultados por pagina; a capacidade de coleta
  vem da navegacao por paginas, nao do aumento artificial de `page_size`.

## Dados retornados

- Campos extraidos:
  - numero CNJ;
  - tipo decisorio;
  - classe;
  - assunto;
  - relator;
  - comarca/origem;
  - orgao julgador;
  - data de publicacao;
  - ementa;
  - URL do documento;
  - `cdAcordao` e `cdForo`.
- Campos canonicos: `CanonicalDecision` e `CanonicalDocument`.
- Inteiro teor: suportado quando a rota publica de arquivo responder.

## Comportamento observado

- Busca com resultado: HTML CJSG parseado pelo provider.
- Busca sem resultado: deve ser separada de erro.
- Controle de acesso: captcha/login deve interromper o fluxo.
- Risco: alto-medio por variacao e-SAJ.

## Fixtures

- [x] Busca com resultado (parser e-SAJ compartilhado com carimbo TJAM).
- [x] Busca vazia (`tests/fixtures/provider_contracts.json#providers/tjam_cjsg/empty`).
- [x] Inteiro teor (contrato de detalhe coberto, com acesso condicionado).
- [x] Controle de acesso (`tests/fixtures/provider_contracts.json#providers/tjam_cjsg/non_success`).
- [x] Paginacao (janela remota de dez itens e sessão cobertas pelo teste offline).

## MCP e agentes

- Quando usar: pesquisa de jurisprudencia publica do TJAM.
- Quando pular: quando a fonte retornar bloqueio, login ou resposta sem
  resultado parseavel.
- Mensagem segura: "A consulta usa rotas publicas do TJAM/CJSG e preserva
  `SourceTrace`."
- Riscos: instabilidade de HTML e-SAJ e eventual controle de acesso.

## Proximos passos

- A fixture e-SAJ é sanitizada e compartilhada; os testes específicos carimbam
  `source=tjam_cjsg` e `court=TJAM`, sem persistir corpo live.
- Labels, vazio e identificadores de detalhe são preservados pelo parser.
- O inteiro teor fica condicionado ao controle de acesso da fonte e à janela
  remota de dez itens por página.

## Validacao live de capacidade - 2026-09-05 (ciclo 51)

- Busca pública `responsabilidade civil`, página 1, dois itens: HTTP 200,
  identidade e resumo presentes, total observado `39.557`.
- O limite de dez itens por página permanece explícito no contrato.
- O detalhe do primeiro registro respondeu com `AccessControlRequiredError`
  por CAPTCHA/controle da fonte; o estado não é tratado como busca vazia.
- A busca textual é elegível para federação; documentos permanecem sob demanda
  quando a fonte os liberar publicamente.

Evidência estruturada (sem corpos):
`docs/provider-discovery/cjsg-live-20260905-cycle51.json`.

### Rechecagem live bounded - 2026-09-13

- A busca pública por `divorcio` respondeu HTTP 200, com um registro parseado
  e total reportado de 749; a evidência está em
  `docs/provider-discovery/tjam-cjsg-live-20260913.json`.
- O detalhe oficial do mesmo registro respondeu HTTP 200, mas apresentou
  CAPTCHA/controle de acesso. O estado foi registrado como
  `access_control_required`, sem tentativa de contorno, em
  `docs/provider-discovery/tjam-cjsg-detail-live-20260913.json`.
- A busca continua válida e federada; o inteiro teor permanece bloqueado e não
  é convertido em vazio.

### Fechamento do contrato local

- `[x]` busca, vazio, erro e acesso controlado classificados;
- `[x]` identidade TJAM/CJSG e identificadores de detalhe validados;
- `[x]` paginação por sessão, limite remoto e ordenação documentados;
- `[x]` trace de fonte e decisão de federação textual registrados.

## Validacao live de capacidade - 2026-08-16

- Consulta: `responsabilidade civil`, duas paginas, 20 itens solicitados.
- Pagina 1: 10 resultados, 10 identificadores unicos, 10 com data.
- Pagina 2: 10 resultados, nenhum identificador repetido, 10 com data.
- Total remoto observado: 39.557.
- Estado: `valid_with_source_page_limit`; a fonte impoe uma janela de 10 itens.
- A mesma janela foi confirmada na Wave 2, com 30 IDs unicos em tres paginas.
- Inteiro teor: capacidade declarada como chamada sob demanda; depende de a
  rota publica `getArquivo.do` responder sem controle adicional.

Evidencia estruturada: `docs/validation/runs/20260816T082800Z-cjsg-capacity-20260816.json`.

### Alinhamento Juscraper (2026-09-01, ciclo 12)

O POST inicial apenas cria a sessao. A pagina 1 e as demais sao carregadas por
`trocaDePagina.do` com a mesma sessao publica.
