# `tjal_cjsg`

## Identidade

- Fonte oficial: Consulta de Jurisprudencia CJSG/e-SAJ do TJAL.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_esaj_cjsg`.
- URL inicial: `https://www2.tjal.jus.br/cjsg`.
- Status de acesso: publico, sujeito a indisponibilidade ou controle da fonte.
- Status no NanoJuris: provider implementado.

## Contrato HTTP

- Rotas conhecidas:
  - `POST /resultadoCompleta.do`
  - `GET /getArquivo.do?cdAcordao=<id>&cdForo=<foro>`
- Metodos: `POST` para busca e `GET` para arquivo publico.
- Parametros: texto integral, ementa/resumo, numero CNJ, intervalo de data e
  tipo de decisao.
- Paginacao: reproduzida em sessao publica com `POST /resultadoCompleta.do`
  seguido de `GET /trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>`.
- O POST inicial somente estabelece a sessao; os resultados vem de
  `trocaDePagina.do`.

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
- Inteiro teor: suportado quando `getArquivo.do` responder publicamente.

## Comportamento observado

- Busca com resultado: HTML CJSG parseado pelo provider.
- Busca sem resultado: deve retornar pagina vazia.
- Controle de acesso: qualquer captcha/login deve ser reportado, sem bypass.
- Risco: alto-medio por variacao e-SAJ.

## Fixtures

- [x] Busca com resultado (parser e-SAJ compartilhado com carimbo TJAL).
- [x] Busca vazia (`tests/fixtures/provider_contracts.json#providers/tjal_cjsg/empty`).
- [x] Inteiro teor (contrato de detalhe coberto, com acesso condicionado).
- [x] Controle de acesso (`tests/fixtures/provider_contracts.json#providers/tjal_cjsg/non_success`).
- [x] Paginacao (sessão e `trocaDePagina.do` cobertas pelo teste offline).

## MCP e agentes

- Quando usar: pesquisa de jurisprudencia publica do TJAL.
- Quando pular: se o retorno nao trouxer container de resultado ou exigir
  validacao humana.
- Mensagem segura: "A fonte TJAL/CJSG foi consultada apenas por rotas publicas
  e sem reutilizar sessao privada."
- Riscos: captcha eventual e layout e-SAJ instavel.

## Proximos passos

- A fixture e-SAJ é sanitizada e compartilhada; os testes específicos carimbam
  `source=tjal_cjsg` e `court=TJAL`, sem persistir corpo live.
- Labels, `cdAcordao` e `cdForo` são preservados pelo parser compartilhado.
- O inteiro teor fica condicionado ao controle de acesso da fonte.

## Validacao live de capacidade - 2026-09-05 (ciclo 51)

- Busca pública `responsabilidade civil`, página 1, dois itens: HTTP 200,
  identidade e resumo presentes, total observado `159.266`.
- O detalhe do primeiro registro respondeu com `AccessControlRequiredError`
  por CAPTCHA/controle da fonte; o estado não é tratado como busca vazia.
- A busca textual é elegível para federação; documentos permanecem sob demanda
  quando a fonte os liberar publicamente.

Evidência estruturada (sem corpos):
`docs/provider-discovery/cjsg-live-20260905-cycle51.json`.

### Fechamento do contrato local

- `[x]` busca, vazio, erro e acesso controlado classificados;
- `[x]` identidade TJAL/CJSG e identificadores de detalhe validados;
- `[x]` paginação por sessão, filtros, ordenação e limites documentados;
- `[x]` trace de fonte e decisão de federação textual registrados.

## Validacao live de capacidade - 2026-08-16

- Consulta: `responsabilidade civil`, duas paginas, 20 itens solicitados.
- Pagina 1: 20 resultados, 20 identificadores unicos, 20 com data.
- Pagina 2: 20 resultados, nenhum identificador repetido, 20 com data.
- Total remoto observado: 157.021.
- Estado: `valid` para a paginacao observada.
- Inteiro teor: capacidade declarada como chamada sob demanda; depende de a
  rota publica `getArquivo.do` responder sem controle adicional.

Evidencia estruturada: `docs/validation/runs/20260816T082800Z-cjsg-capacity-20260816.json`.

### Alinhamento Juscraper (2026-09-01, ciclo 12)

O fluxo eSAJ usa POST de submissao seguido por GET da pagina 1 e da pagina
solicitada em `trocaDePagina.do`, mantendo a sessao e sem contornar acesso.
