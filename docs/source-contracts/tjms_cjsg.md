# `tjms_cjsg`

## Identidade

- Fonte oficial: Consulta de Jurisprudencia CJSG/e-SAJ do TJMS.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `html_esaj_cjsg`.
- URL inicial: `https://esaj.tjms.jus.br/cjsg`.
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
- Inteiro teor: suportado quando `getArquivo.do` estiver publico.

## Comportamento observado

- Busca com resultado: usa parser compartilhado da familia CJSG/e-SAJ.
- Busca sem resultado: deve retornar vazio.
- Controle de acesso: sem bypass.
- Risco: medio-alto por variacao e-SAJ.

## Fixtures

- [x] Busca com resultado (`tests/fixtures/tjsp_cjsg_result.html`, parser
  compartilhado e carimbo especifico TJMS).
- [x] Busca vazia (`tests/fixtures/provider_contracts.json#providers/tjms_cjsg/empty`).
- [x] Inteiro teor (`tests/fixtures/provider_contracts.json#providers/tjms_cjsg/success`;
  HTML e PDF cobertos pelo teste de contrato).
- [x] Controle de acesso (`tests/fixtures/provider_contracts.json#providers/tjms_cjsg/non_success`).
- [x] Paginacao (`tests/fixtures/provider_contracts.json#providers/tjms_cjsg/success`;
  sessao publica e rota `trocaDePagina.do` cobertas pelo teste offline).

## MCP e agentes

- Quando usar: pesquisa de jurisprudencia publica do TJMS.
- Quando pular: se houver captcha, login ou pagina de sessao vazia.
- Mensagem segura: "A consulta usa jurisprudencia publica do TJMS/CJSG e
  preserva metadados de origem."
- Riscos: tratar bloqueio como erro de parser.

## Proximos passos

- A fixture e-SAJ compartilhada e deliberadamente sanitizada; os testes
  especificos carimbam `source=tjms_cjsg` e `court=TJMS`, evitando persistir
  corpos da fonte. Nao ha pendencia de contrato para promover a busca.
- Revalidar periodicamente a disponibilidade do detalhe e a extracao de PDFs;
  um PDF publico pode ser retornado sem camada de texto (OCR continua fora do
  adapter).

## Validacao live de capacidade - 2026-08-16

- Consulta: `responsabilidade civil`, duas paginas, 20 itens solicitados.
- Pagina 1: 20 resultados, 20 identificadores unicos, 20 com data.
- Pagina 2: 20 resultados, nenhum identificador repetido, 20 com data.
- Total remoto observado: 229.013.
- Estado: `valid` para a paginacao observada.
- Inteiro teor: capacidade declarada como chamada sob demanda; depende de a
  rota publica `getArquivo.do` responder sem controle adicional.

Evidencia estruturada: `docs/validation/runs/20260816T082800Z-cjsg-capacity-20260816.json`.

### Alinhamento Juscraper (2026-09-01, ciclo 12)

O POST de `resultadoCompleta.do` e tratado como ack; a resposta e obtida por
GETs de `trocaDePagina.do` para pagina 1 e pagina solicitada na mesma sessao.

## Validacao live de capacidade - 2026-09-05 (ciclo 51)

- Consulta publica: `responsabilidade civil`, pagina 1, dois itens.
- Busca: HTTP 200, dois registros com identidade e resumo, total remoto
  observado `230.539` (o valor pode variar entre execucoes).
- Inteiro teor: `getArquivo.do` respondeu HTTP 200 com PDF de 475.946 bytes;
  a extracao foi classificada como `partial` e sem texto selecionavel, mas o
  hash, MIME e bytes foram preservados no `SourceTrace`.
- A evidencia da mesma chamada tambem revalidou TJAC, TJAL e TJAM: as buscas
  retornaram dados, enquanto os detalhes responderam com
  `AccessControlRequiredError` por captcha/controle da fonte. Esse estado e
  explicito e nao e convertido em vazio nem contornado.

Evidencia estruturada (sem corpos):
`docs/provider-discovery/cjsg-live-20260905-cycle51.json`.

### Fechamento do contrato local

- `[x]` busca com resultado, busca vazia e falha HTTP classificadas;
- `[x]` identidade TJMS/CJSG e identificadores `cdAcordao`/`cdForo` validados;
- `[x]` paginação por sessão reproduzida em teste de contrato;
- `[x]` detalhe HTML/PDF, MIME, tamanho, hash e extração parcial preservados;
- `[x]` controle de acesso sem bypass e com erro tipado;
- `[x]` filtros textuais, número, datas, tipos e ordenação mapeados;
- `[x]` trace e política de limites documentados.
